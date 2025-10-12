#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, QoSProfile, QoSDurabilityPolicy

from ackermann_msgs.msg import AckermannDriveStamped
from vision_msgs.msg import Detection2DArray, LabelInfo

from ros2_numpy import from_detection2d_array, from_label_info

from drive_manager.srv import SetMode 

class DriveManager(Node):
    def __init__(self):
        super().__init__('drive_manager')

        # Set up QoS for label mapping (transient local)
        qos_transient = QoSProfile(depth=1)
        qos_transient.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        
        # Create a custom service
        self.srv = self.create_service(SetMode, 'set_mode', self.update_mode)
        
        # List of valid mode options
        self.modes = [
            '/pilotnet/ackermann_cmd',
            '/parking/ackermann_cmd',
            '/rc/ackermann_cmd']


        # Label mapping subscription
        self.label_sub = self.create_subscription(
            LabelInfo,
            '/label_mapping',
            self.label_mapping_callback,
            qos_transient
        )
    
        # Define Quality of Service (QoS) for communication
        self.qos_profile = qos_profile_sensor_data
        self.qos_profile.depth = 1

        # Init default mode
        self.mode = '/rc/ackermann_cmd'

        # Subscribe to RC command
        self.cmd_sub = None
        self.update_subscription(self.mode)

        # Publisher for autonomous topic
        self.cmd_pub = self.create_publisher(
            AckermannDriveStamped,
            '/autonomous/ackermann_cmd',
            self.qos_profile
        )

    def update_mode(self, request, response):
        # If the requested mode is already active
        if request.mode == self.mode:
            self.get_logger().info(f"Already in mode: {self.mode}")
            response.success = True
            return response

        # If the requested mode is valid
        if request.mode in self.modes:
            self.mode = request.mode
            self.update_subscription(self.mode) # UPDATE
            self.get_logger().info(f"Switched to mode: {self.mode}")
            response.success = True
        else:
            self.get_logger().warn(
                f"Mode switch failed. Available modes: {', '.join(self.modes)}"
            )
            response.success = False

        return response

    def update_subscription(self, topic):
        # Update the AckermannDrive subscription.
        # Destroy the existing subscription first.
        if not self.cmd_sub is None:
            self.destroy_subscription(self.cmd_sub)

        # Create a new one
        self.cmd_sub = self.create_subscription(
            AckermannDriveStamped,
            topic,
            self.drive_callback,
            self.qos_profile
        )

    def label_mapping_callback(self, msg: LabelInfo):
        self.id2label = from_label_info(msg)
        self.label2id = {lbl: idx for idx, lbl in self.id2label.items()}
        self.get_logger().info(f"Label mapping received: {self.id2label}")

        self.setup_callbacks()

    def setup_detection_callback(self):

        # Setup detection subscription
        self.det_sub = self.create_subscription(
            Detection2DArray,
            '/detections_2d',
            self.detection_callback,
            self.qos_profile
        )


    def detection_callback(self, msg: Detection2DArray):
        detections = from_detection2d_array(msg)
        self.get_logger().info(f"Detections: {detections}")

    def drive_callback(self, msg: AckermannDriveStamped):
        # Forward the message to /autonomous/ackermann_cmd
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
