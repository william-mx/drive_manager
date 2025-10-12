from setuptools import setup
import os
from glob import glob

package_name = 'drive_manager'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        # Install package resource index
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        # Install package manifest
        ('share/' + package_name, ['package.xml']),
        # Install launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your@email.com',
    description='Drive manager node that forwards ackermann commands and processes detections.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'drive_manager_node = drive_manager.drive_manager_node:main',
        ],
    },
)
