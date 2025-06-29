from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'topic',
            default_value='/rc/ackermann_cmd',
            description='Topic to publish AckermannDriveStamped commands to.'
        ),

        Node(
            package='drive_manager',
            executable='drive_manager',
            name='drive_manager_node',
            output='screen',
            remappings=[
                ('/rc/ackermann_cmd', LaunchConfiguration('topic'))
            ]
        )
    ])
