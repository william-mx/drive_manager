from drive_manager.srv import SetMode 


def call_set_mode_service(node, mode: str):
    # Create a client for the 'set_mode' service
    client = node.create_client(SetMode, 'set_mode')

    # Wait until available
    while not client.wait_for_service(timeout_sec=1.0):
        node.get_logger().info('SetMode service not available, waiting again...')

    # Create and populate the request
    request = SetMode.Request()
    request.mode = mode

    # Call asynchronously
    future = client.call_async(request)

    # Handle result when done
    future.add_done_callback(lambda f: _set_mode_callback(f, node))


def _set_mode_callback(future, node):
    try:
        response = future.result()
        if response.success:
            node.get_logger().info("SetMode successful")
        else:
            node.get_logger().warn("SetMode failed")
    except Exception as e:
        node.get_logger().error(f"SetMode service call failed: {e}")
