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

def send_request(client_socket, command, path="", save_path=""):
    request = json.dumps({'command': command, 'path': path})
    client_socket.send(request.encode())

    if command == "exit":
        return ResponseStatus.SUCCESS
    response = receive_json_response(client_socket)

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
        receive_file_data(client_socket, save_path, response["size"])
        return ResponseStatus.SUCCESS
    return ResponseStatus.OTHER_ERROR



def receive_json_response(client_socket):
    response_data = ''
    while True:
        part = client_socket.recv(4096).decode()
        response_data += part
        if len(part) < 4096:
            break
    return json.loads(response_data)


def receive_file_data(client_socket, save_path, file_size):
    # Tworzenie katalogów jeśli nie isnieją

    if('/' in save_path):
        os.makedirs(os.path.dirname(save_path), exist_ok = True)

    with open(save_path, 'wb') as file:  # binarnie
        received_size = 0
        while received_size < file_size:
            data = client_socket.recv(4096)
            file.write(data)
            received_size += len(data)


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
            if command[0] == 'exit':
                send_request(client_socket, command[0])
                break
            elif command[0] in ['ls', 'tree']:
                path = command[1] if len(command) >= 2 else "."
                send_request(client_socket, command[0], path)
            elif command[0] == 'get':
                if len(command) != 3:
                    print(f"niepoprawna liczba parametrów")
                    continue
                path = command[1]
                save_path = command[2]
                send_request(client_socket, command[0], path, save_path)
            elif command[0] == 'help':
                print_instructions()
            else:
                print("Nieznana komenda.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('host', help='Server host')
    parser.add_argument('--port', default=65432, type=int, help='Server port')
    args = parser.parse_args()
    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
