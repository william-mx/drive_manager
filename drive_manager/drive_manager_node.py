#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from mxck_interfaces.srv import SetMode

from ackermann_msgs.msg import AckermannDriveStamped
from std_msgs.msg import Float32

DEFAULT_MAX_SPEED = 2.0  # m/s — applied when no speed limit is active


from drive_manager.srv import SetMode 

class DriveManager(Node):
    def __init__(self):
        super().__init__('drive_manager')

        # Define Quality of Service (QoS) for communication
        self.qos_profile = qos_profile_sensor_data
        self.qos_profile.depth = 1

        # List of valid mode options
        self.modes = [
            '/follower/ackermann_cmd',
            '/pilotnet/ackermann_cmd',
            '/parking/ackermann_cmd',
            '/rc/ackermann_cmd',
        ]

        # Init default mode and speed limit
        self.mode = '/rc/ackermann_cmd'
        self.max_speed = DEFAULT_MAX_SPEED

        # Mode switch service
        self.srv = self.create_service(SetMode, 'set_mode', self.update_mode)

        # Subscribe to the active drive source (default: RC)
        self.cmd_sub = None
        self.update_subscription(self.mode)

        # Subscribe to speed limit from perception policy node
        self.speed_limit_sub = self.create_subscription(
            Float32,
            '/speed_limit',
            self.speed_limit_callback,
            self.qos_profile,
        )

        # Publisher for downstream autonomous command
        self.cmd_pub = self.create_publisher(
            AckermannDriveStamped,
            '/autonomous/ackermann_cmd',
            self.qos_profile,
        )

    # ------------------------------------------------------------------ #
    #  Mode switching                                                       #
    # ------------------------------------------------------------------ #

    def update_mode(self, request, response):
        if request.mode == self.mode:
            self.get_logger().info(f"Already in mode: {self.mode}")
            response.success = True
            return response

        if request.mode in self.modes:
            self.mode = request.mode
            self.update_subscription(self.mode)
            self.get_logger().info(f"Switched to mode: {self.mode}")
            response.success = True
        else:
            self.get_logger().warn(
                f"Mode switch failed. Available modes: {', '.join(self.modes)}"
            )
            response.success = False

        return response

    def update_subscription(self, topic):
        """Swap the AckermannDrive subscription to the new source topic."""
        if self.cmd_sub is not None:
            self.destroy_subscription(self.cmd_sub)

        self.cmd_sub = self.create_subscription(
            AckermannDriveStamped,
            topic,
            self.drive_callback,
            self.qos_profile,
        )

    # ------------------------------------------------------------------ #
    #  Callbacks                                                            #
    # ------------------------------------------------------------------ #

    def speed_limit_callback(self, msg: Float32):
        """Update the active speed cap received from the perception policy."""
        self.max_speed = msg.data
        self.get_logger().debug(f"Speed limit updated: {self.max_speed:.2f} m/s")

    def drive_callback(self, msg: AckermannDriveStamped):
        """Clamp speed to the current limit, then forward to /autonomous."""
        msg.drive.speed = min(msg.drive.speed, self.max_speed)

        self.cmd_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = DriveManager()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().warn("KeyboardInterrupt: shutting down.")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()