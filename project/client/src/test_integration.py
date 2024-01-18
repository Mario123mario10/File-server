import json
import os.path
import socket
import tarfile
from typing import Dict, AnyStr
import tempfile

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_container_is_ready

from client import receive_json_response, send_request, ResponseStatus


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
def test_response_correct(container, server_host, server_port):
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
def test_response_wrong_path(container, server_host, server_port):
    data = "test contents"
    save_path = "doesNotExist.txt"
    put_files(container, {
        "server-files/test.txt": data,
    })
    command = 'get'
    path = '../src/server.py'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))

        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)

        assert response["status"] == "error"
        assert response["message"] == "Niepoprawna ścieżka"

@container_wrapper
def test_get_wrong_file(container, server_host, server_port):
    data = "test contents"
    save_path = "doesNotExist.txt"
    put_files(container, {
        "server-files/test.txt": data,
    })
    command = 'get'
    path = 'doesNotExist.txt'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))

        returned = send_request(client_socket, command, path, save_path)

        dir_iterator = os.scandir()
        file_list = []
        for entry in dir_iterator :
            if entry.is_dir() or entry.is_file():
                file_list.append(entry.name)
        assert save_path not in file_list
        assert returned == ResponseStatus.STATUS_ERROR

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
        returned = send_request(client_socket, command, path, save_path)

        file_stats = os.stat(save_path)

        assert file_stats.st_size == len(data)
        assert returned == ResponseStatus.SUCCESS

@container_wrapper
def test_get_correct_check_file_size(container, server_host, server_port):
    data = "test contents"
    command = 'get'
    path = 'test.txt'
    save_path = "odpowiedz.txt"
    put_files(container, {
        "server-files/" + path : data,
    })
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        returned = send_request(client_socket, command, path, save_path)

        dir_iterator = os.scandir()
        file_list = []
        for entry in dir_iterator :
            if entry.is_dir() or entry.is_file():
                file_list.append(entry.name)
        assert save_path in file_list
        assert returned == ResponseStatus.SUCCESS

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
        returned = send_request(client_socket, command, path, save_path)

        dir_iterator = os.scandir(new_folder)
        file_list = []
        for entry in dir_iterator :
            if entry.is_dir() or entry.is_file():
                file_list.append(entry.name)
        assert new_file_name in file_list
        assert returned == ResponseStatus.SUCCESS

@container_wrapper
def test_get_from_subfolder(container, server_host, server_port):
    data = "test contents"
    subfolder_name = "subfolder"
    server_file_path =  subfolder_name + "/test.txt"
    command = 'get'
    save_path = "z_glebi.txt"
    put_files(container, {
       "server-files/" + server_file_path : data,
    })
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        send_request(client_socket, command, server_file_path, save_path)

        dir_iterator = os.scandir()
        file_list = []
        for entry in dir_iterator :
            if entry.is_dir() or entry.is_file():
                file_list.append(entry.name)
        assert save_path in file_list

@container_wrapper
def test_ls_single(container, server_host, server_port):
    put_files(container, {
        "server-files/test.txt": "test contents",
    })
    command = 'ls'
    path = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)

        assert response["status"] == "ok"
        assert response["data"] == "test.txt"

@container_wrapper
def test_ls_from_subfolder(container, server_host, server_port):
    put_files(container, {
        "server-files/test.txt": "test contents",
        "server-files/folder/cos.txt":"cos innego"
,    })
    command = 'ls'
    path = 'folder'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)

        assert response["status"] == "ok"
        assert response["data"] == "cos.txt"


@container_wrapper
def test_ls_multiple(container, server_host, server_port):
    put_files(container, {
        "server-files/test.txt": "test contents",
        "server-files/test2.txt": "test contents",
        "server-files/test3.txt": "test contents",
    })
    command = 'ls'
    path = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)

        assert response["status"] == "ok"
        assert response["data"] == "test2.txt\ntest.txt\ntest3.txt"

@container_wrapper
def test_ls_wrong_catalogue(container, server_host, server_port):
    put_files(container, {
        "server-files/test.txt": "test contents",
    })
    command = 'ls'
    path = 'badPath'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)

        assert response["status"] == "error"
        assert response["message"] == "Katalog nie znaleziony"

@container_wrapper
def test_tree_from_subfolder(container, server_host, server_port):
    put_files(container, {
        "server-files/test.txt": "test contents",
        "server-files/folder/cos.txt": "cos innego"
,    })
    command = 'tree'
    path = 'folder'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)

        assert response["status"] == "ok"
        assert response["data"]=="cos.txt\n"

@container_wrapper
def test_tree_from_main(container, server_host, server_port):
    put_files(container, {
        "server-files/subfolder/hidden.txt":"cos innego",
        "server-files/hello.txt": "test contents",
        })

    command = 'tree'
    path = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)

        assert response["status"] == "ok"
        assert response["data"] == "subfolder\n  hidden.txt\nhello.txt\n"

@container_wrapper
def test_tree_folder_does_not_exist(container, server_host, server_port):
    put_files(container, {
        "server-files/main.txt": "test contents",
        })

    command = 'tree'
    path = 'doesNotExist'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        request = json.dumps({'command': command, 'path': path})
        client_socket.send(request.encode())

        response = receive_json_response(client_socket)

        assert response["status"] == "error"
        assert response["message"] == "Katalog nie znaleziony"