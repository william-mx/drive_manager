from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='drive_manager',
            executable='drive_manager_node',
            name='drive_manager',
            output='screen',
        )
    ])