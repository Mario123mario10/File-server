from enum import Enum
import socket
import json
import argparse
import os

class ResponseStatus(Enum):
    SUCCESS = 0
    STATUS_ERROR = 1
    INCORRECT_INQUIRY = 2
    OTHER_ERROR = 3


class ConnectionClosed(Exception):
    ...


def send_request(client_socket, command, path="", save_path=""):
    request = json.dumps({'command': command, 'path': path})
    client_socket.send((request + "\n").encode())

    if command == "exit":
        return ResponseStatus.SUCCESS
    response, rest = receive_json_response(client_socket)

    if response["status"] == "error":
        print(response["message"])
        return ResponseStatus.STATUS_ERROR

    if command in ['ls', 'tree']:
        if "data" in response:
            print(response["data"])
            return ResponseStatus.SUCCESS
        else:
            print("Brak danych do wyświetlenia.")
            return ResponseStatus.INCORRECT_INQUIRY

    elif command == 'get':
        if os.path.isdir(save_path):
            print("Niepoprawna ścieżka: wskazuje na istniejący folder")
            return ResponseStatus.INCORRECT_INQUIRY
        if not "size" in response:
            print("Brak danych pliku do pobrania.") # @TODO czy kiedykolwiek do tej linii w kodzie dojdziemy?
            return ResponseStatus.INCORRECT_INQUIRY
        receive_file_data(client_socket, save_path, response["size"], rest)
        return ResponseStatus.SUCCESS
    return ResponseStatus.OTHER_ERROR



def receive_json_response(client_socket):
    json_string = ''
    while True:
        data = client_socket.recv(4096)
        if not data:
            raise ConnectionClosed()
        decoded_data = data.decode()
        if '\n' in decoded_data:
            json_string += decoded_data[:decoded_data.find('\n')]
            return json.loads(json_string), data[data.index(b'\n') + 1:]


def receive_file_data(client_socket, save_path, file_size, initial_data):
    # Tworzenie katalogów jeśli nie isnieją

    if('/' in save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok = True)

    with open(save_path, 'wb') as file:  # binarnie
        if initial_data:
            file.write(initial_data)
        received_size = len(initial_data)
        while received_size < file_size:
            data = client_socket.recv(4096)
            if not data:
                raise ConnectionClosed()
            file.write(data)
            received_size += len(data)
        print(f"Pobrano {received_size} bajtów")


INSTRUCTIONS = [
    ("get <ścieżka na serwerze> <ścieżka gdzie zapisać>", "Pobiera plik z serwera"),
    ("ls [<ścieżka>]", "Wyświetla zawartość folderu"),
    ("tree [<ścieżka>]", "Wyświetla drzewo folderów"),
    ("help", "Wyświetla dostępne komendy"),
    ("exit", "Zamyka program")
]


def print_instructions():
    print("Dostępne komendy:")
    max_command_length = max([len(instruction[0]) for instruction in INSTRUCTIONS])
    for instruction in INSTRUCTIONS:
        print(f"  {instruction[0]:<{max_command_length+3}}{instruction[1]}")


def run_client(server_host, server_port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        print_instructions()
        while True:
            command = input("> ")
            command = command.split(' ')
            try:
                if command[0] == 'exit':
                    send_request(client_socket, command[0])
                    break
                elif command[0] in ['ls', 'tree']:
                    path = command[1] if len(command) >= 2 else "."
                    send_request(client_socket, command[0], path)
                elif command[0] == 'get':
                    if len(command) < 2:
                        print(f"niepoprawna liczba parametrów")
                        continue
                    if len(command) < 3:
                        save_path = os.getcwd() + '/' + command[1].split('/')[-1]
                    elif os.path.isdir(command[2]):
                        save_path = command[2] + '/' + command[1].split('/')[-1]
                    else:
                        save_path = command[2]
                    path = command[1]
                    send_request(client_socket, command[0], path, save_path)
                elif command[0] == 'help':
                    print_instructions()
                else:
                    print("Nieznana komenda.")
            except ConnectionClosed as e:
                print(f"Połączenie zostało zamknięte")
                break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='Server host')
    parser.add_argument('--port', default=65432, type=int, help='Server port')
    args = parser.parse_args()
    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
