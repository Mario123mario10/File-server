import json
import os.path
import socket
import tarfile
from typing import Dict, AnyStr
import tempfile

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_container_is_ready

from client import receive_json_response, send_request


def prepare_server_container():
    return (DockerContainer(image="python:3.11")
            .with_volume_mapping(os.path.abspath("../server/src"), "/server-src")
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
def test_response(container, server_host, server_port):
    data = "test contents"
    put_files(container, {
        "server-files/test.txt": data,
    })
    command = 'get'
    path = 'test.txt'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)
        assert response["status"] == "ok"
        assert response["size"] == len(data)


@container_wrapper
def test_get_correct_save_in_base_folder(container, server_host, server_port):
    data = "test contents"
    command = 'get'
    path = 'test.txt'
    save_path = "odpowiedz.txt"
    put_files(container, {
        "server-files/" + path : data,
    })
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        send_request(client_socket, command, path, save_path)

        dir_iterator = os.scandir()
        file_list = []
        for entry in dir_iterator :
            if entry.is_dir() or entry.is_file():
                file_list.append(entry.name)
        assert save_path in file_list

@container_wrapper
def test_get_correct_save_in_new_folder(container, server_host, server_port):
    data = "test contents"
    command = 'get'
    path = 'test.txt'
    new_folder = "newFolder"
    new_file_name = "odpowiedz.txt"
    save_path =  new_folder + '/' + new_file_name
    put_files(container, {
        "server-files/" + path : data,
    })
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        send_request(client_socket, command, path, save_path)

        dir_iterator = os.scandir(new_folder)
        file_list = []
        for entry in dir_iterator :
            if entry.is_dir() or entry.is_file():
                file_list.append(entry.name)
        assert new_file_name in file_list

# @container_wrapper
# def test_get_from_subfolder(container, server_host, server_port):
#     data = "test contents"
#     subfolder_name = "subfolder"
#     server_file_path =  subfolder_name + "/test.txt"
#     command = 'get'
#     save_path = "z_glebi.txt"
#     put_files(container, {
#        "server-files/" + server_file_path : data,
#     })
#     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
#         client_socket.connect((server_host, server_port))
#         send_request(client_socket, command, server_file_path, save_path)

#         dir_iterator = os.scandir()
#         file_list = []
#         for entry in dir_iterator :
#             if entry.is_dir() or entry.is_file():
#                 file_list.append(entry.name)
#         assert save_path in file_list
