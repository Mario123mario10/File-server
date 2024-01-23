import socket
import threading
import os
import json
import time
import os
import argparse

BASE_PATH = ''


def verify_file_path(requested_path):
    # Uzyskanie bezwzględnej ścieżki do żądanego pliku
    absolute_requested_path = os.path.abspath(requested_path)
    # Sprawdzenie, czy żądana ścieżka znajduje się w obrębie bazowej ścieżki
    return os.path.commonprefix([BASE_PATH, absolute_requested_path]) == BASE_PATH


class ConnectionClosed(Exception):
    ...


def receive_json_response(client_socket):
    json_string = ''
    while True:
        data = client_socket.recv(4096)
        if not data:
            raise ConnectionClosed("Połączenie zostało zamknięte przez klienta.")
        decoded_data = data.decode()
        if '\n' in decoded_data:
            json_string += decoded_data[:decoded_data.find('\n')]
            return json.loads(json_string)


def handle_client(connection, address):
    print(f"Połączenie z {address} zostało nawiązane.")
    while True:
        try:
            request = receive_json_response(connection)
            command = request['command']
            path = request['path']
            print(f"{address}: Otrzymano {command} {path}")
            if command == 'get':
                send_file(connection, path)
            elif command == 'ls':
                send_ls(connection, path)
            elif command == 'tree':
                send_tree(connection, path)
            else: #exit
                break
        except Exception as e:
            print(f"Wystąpił błąd: {e}")
            break
    connection.close()
    print(f"Połączenie z {address} zostało zamknięte.")


def send_file(connection, requested_path):
    full_path = os.path.join(BASE_PATH, requested_path)

    if not verify_file_path(full_path):
        connection.sendall((json.dumps({"status": "error", "message": "Niepoprawna ścieżka"}) + "\n").encode())
    elif not os.path.isfile(full_path):
        connection.sendall((json.dumps({"status": "error", "message": "Plik nie znaleziony"}) + "\n").encode())
    else:
        file_size = os.path.getsize(full_path)
        connection.sendall((json.dumps({"status": "ok", "size": file_size}) + "\n").encode())

        with open(full_path, 'rb') as file:
            data = file.read(4096)
            while data:
                connection.sendall(data)
                data = file.read(4096)


def send_ls(connection, requested_path):
    full_path = os.path.join(BASE_PATH, requested_path)

    if not verify_file_path(full_path):
        connection.sendall((json.dumps({"status": "error", "message": "Niepoprawna ścieżka"}) + "\n").encode())
    elif not os.path.isdir(full_path):
        connection.sendall((json.dumps({"status": "error", "message": "Katalog nie znaleziony"}) + "\n").encode())
    else:
        try:
            files = os.listdir(full_path)
            data = '\n'.join(files)
            response = json.dumps({"status": "ok", "data": data})
            connection.sendall((response + "\n").encode())
        except Exception as e:
            error_message = f"Błąd: {e}"
            connection.sendall((json.dumps({"status": "error", "message": error_message}) + "\n").encode())


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

    full_path = os.path.join(BASE_PATH, requested_path)

    if not verify_file_path(full_path):
        connection.sendall((json.dumps({"status": "error", "message": "Niepoprawna ścieżka"}) + "\n").encode())
    elif not os.path.isdir(full_path):
        connection.sendall((json.dumps({"status": "error", "message": "Katalog nie znaleziony"}) + "\n").encode())
    else:
        try:
            tree_list = []
            generate_tree(full_path, indent, tree_list)
            tree_data = ''.join(tree_list)
            response = json.dumps({"status": "ok", "data": tree_data})
            connection.sendall((response + "\n").encode())
        except Exception as e:
            error_message = f"Błąd: {e}"
            connection.sendall((json.dumps({"status": "error", "message": error_message}) + "\n").encode())
			
    


def start_server(host, port):
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('base_path', help='Ścieżka bazowa serwera plików')
    parser.add_argument('--host', default='127.0.0.1', help='Adres nasłuchu serwera')
    parser.add_argument('--port', default=65432, help='Port nasłuchu serwera')
    args = parser.parse_args()
    global BASE_PATH
    BASE_PATH = os.path.abspath(args.base_path)
    if not os.path.isdir(BASE_PATH):
        print(f"Niepoprawna ścieżka base_path: nie wskazuje na istniejący folder")
        return
    start_server(args.host, int(args.port))


if __name__ == '__main__':
    main()
