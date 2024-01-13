import json
import os.path
import socket
import tarfile
from typing import Dict, AnyStr
import tempfile

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_container_is_ready

from client import receive_json_response


def prepare_server_container():
    return (DockerContainer(image="python:3.11")
            .with_volume_mapping(os.path.abspath("../server/"), "/server-src")
            .with_command(f"python3 /server-src/server.py /server-files/ --host 0.0.0.0 --port 65432")
            .with_exposed_ports(65432))


def put_files(container, files: Dict[str, AnyStr]):
    tar_handle, tar_path = tempfile.mkstemp()
    with tarfile.open(tar_path, "w") as tar:
        for path, contents in files.items():
            temp_handle, temp_path = tempfile.mkstemp()
            with open(temp_handle, "w") as temp_file:
                temp_file.write(contents)
            tar.add(temp_path, arcname=path)
    with open(tar_path, "rb") as fd:
        container.get_wrapped_container().put_archive("/", data=fd)


def container_wrapper(func):

    @wait_container_is_ready()
    def wait_container_func(*args, **kwargs):
        func(*args, **kwargs)

    def wrapper():
        container = prepare_server_container()
        with container as container:
            server_host = container.get_container_host_ip()
            server_port = int(container.get_exposed_port(65432))
            wait_container_func(container, server_host, server_port)
    return wrapper


@container_wrapper
def test_demo(container, server_host, server_port):
    put_files(container, {
        "server-files/test.txt": "test contents",
    })
    command = 'get'
    path = 'test.txt'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)
        assert response["status"] == "ok"
