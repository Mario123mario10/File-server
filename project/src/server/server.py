import socket
import threading
import os
import json
import time
import os

# Ustaw bazową ścieżkę na katalog, w którym znajduje się plik serwera
base_path = os.path.dirname(os.path.realpath(__file__))


def verify_file_path(requested_path):
    # Uzyskanie bezwzględnej ścieżki do żądanego pliku
    absolute_requested_path = os.path.abspath(requested_path)
    # Sprawdzenie, czy żądana ścieżka znajduje się w obrębie bazowej ścieżki
    return os.path.commonprefix([base_path, absolute_requested_path]) == base_path


def handle_client(connection, address):
    print(f"Połączenie z {address} zostało nawiązane.")
    while True:
        try:
            data = connection.recv(1024).decode()
            if not data:
                break
            request = json.loads(data)
            command = request['command']
            path = request['path']

            if command == 'get':
                send_file(connection, path)
            elif command == 'ls':
                send_ls(connection, path)
            elif command == 'tree':
                send_tree(connection, path)
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            break
    connection.close()


def send_file(connection, requested_path):
    full_path = os.path.join(base_path, requested_path)

    if not verify_file_path(full_path):
        connection.sendall(json.dumps({"status": "error", "message": "Niepoprawna ścieżka"}).encode())
    elif not os.path.isfile(full_path):
        connection.sendall(json.dumps({"status": "error", "message": "Plik nie znaleziony"}).encode())
    else:
        file_size = os.path.getsize(full_path)
        connection.sendall(json.dumps({"status": "ok", "size": file_size}).encode())

        with open(full_path, 'rb') as file:
            data = file.read(4096)
            while data:
                connection.sendall(data)
                data = file.read(4096)


def send_ls(connection, requested_path):
    full_path = os.path.join(base_path, requested_path)

    if not verify_file_path(full_path):
        connection.sendall(json.dumps({"status": "error", "message": "Niepoprawna ścieżka"}).encode())
    elif not os.path.isdir(full_path):
        connection.sendall(json.dumps({"status": "error", "message": "Katalog nie znaleziony"}).encode())
    else:
        try:
            files = os.listdir(full_path)
            data = '\n'.join(files)
            response = json.dumps({"status": "ok", "data": data})
            connection.sendall(response.encode())
        except Exception as e:
            error_message = f"Błąd: {e}"
            connection.sendall(json.dumps({"status": "error", "message": error_message}).encode())


def send_tree(connection, requested_path, indent=''):
    def generate_tree(path, indent, tree_list):
        if os.path.isdir(path):
            try:
                files = os.listdir(path)
                for f in files:
                    tree_list.append(indent + f + '\n')
                    file_path = os.path.join(path, f)
                    if os.path.isdir(file_path):
                        generate_tree(file_path, indent + "  ", tree_list)
            except Exception as e:
                tree_list.append("Błąd: " + str(e) + '\n')
        else:
            tree_list.append("Katalog nie znaleziony\n")

    full_path = os.path.join(base_path, requested_path)

    if verify_file_path(full_path):
        tree_list = []
        generate_tree(full_path, indent, tree_list)
        tree_data = ''.join(tree_list)
        response = json.dumps({"status": "ok", "data": tree_data})
        connection.sendall(response.encode())
    else:
        connection.sendall(json.dumps({"status": "error", "message": "Niepoprawna ścieżka"}).encode())


def start_server(host='127.0.0.1', port=65432):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)  # Zwiększenie rozmiaru bufora odbiorczego (RCV)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)  # Zwiększenie rozmiaru bufora nadawczego (SND)
    server.bind((host, port))
    server.listen()
    print(f"Serwer nasłuchuje na {host}:{port}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


# Uruchom serwer
if __name__ == '__main__':
    start_server()
