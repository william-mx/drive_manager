import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data, QoSProfile, QoSDurabilityPolicy

from ackermann_msgs.msg import AckermannDriveStamped
from vision_msgs.msg import Detection2DArray, LabelInfo

from ros2_numpy import from_detection2d_array, from_label_info

class DriveManager(Node):
    def __init__(self):
        super().__init__('drive_manager')

        # Set up QoS for label mapping (transient local)
        qos_transient = QoSProfile(depth=1)
        qos_transient.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL

        # Label mapping subscription
        self.label_sub = self.create_subscription(
            LabelInfo,
            '/label_mapping',
            self.label_mapping_callback,
            qos_transient
        )

    def label_mapping_callback(self, msg: LabelInfo):
        self.id2label = from_label_info(msg)
        self.label2id = {lbl: idx for idx, lbl in self.id2label.items()}
        self.get_logger().info(f"Label mapping received: {self.id2label}")

        self.setup_callbacks()

    def setup_callbacks(self):
        # Define Quality of Service (QoS) for communication
        qos_profile = qos_profile_sensor_data
        qos_profile.depth = 1

        # Setup detection subscription
        self.det_sub = self.create_subscription(
            Detection2DArray,
            '/detections_2d',
            self.detection_callback,
            qos_profile
        )

        # Subscribe to RC command
        self.cmd_sub = self.create_subscription(
            AckermannDriveStamped,
            '/rc/ackermann_cmd',
            self.drive_callback,
            qos_profile
        )

        # Publisher for autonomous topic
        self.cmd_pub = self.create_publisher(
            AckermannDriveStamped,
            '/autonomous/ackermann_cmd',
            qos_profile
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
