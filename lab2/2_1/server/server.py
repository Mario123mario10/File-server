# simple Python socket server
# (C) Imie Naziwsko 2023 [PSI]

import socket
import sys
import struct

def is_printable_ascii(data):
    return all(32 <= byte <= 126 for byte in data)

def main():
    if len(sys.argv) < 2:
        print("No port provided, using default 8000")
        PORT = 8000
    else:
        PORT = int(sys.argv[1])

    HOST = '127.0.0.1'  # Address unspecified
    BUFSIZE = 512

    print("Will listen on ", HOST, ":", PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            expected_packet_number = 0

            while True:
                data = conn.recv(BUFSIZE)
                if not data:
                    break

                packet_number, data_length = struct.unpack('!Ih', data[:6])
                message_data = data[6:6+data_length]
                received_length = len(data)

                if packet_number != expected_packet_number:
                    print(f"Missing packet! Expected {expected_packet_number}, received {packet_number}")
                    conn.sendall(b'Missing packet')
                    expected_packet_number = packet_number + 1
                    continue

                if received_length != data_length + 6:
                    print(f"Incorrect data length. Expected {data_length + 6}, received {received_length}")
                    conn.sendall(b'Incorrect data length')
                    continue

                if not is_printable_ascii(message_data):
                    print("Data is not printable ASCII")
                    conn.sendall(b'Data is not printable ASCII')
                    continue

                print(f"\nReceived packet # {packet_number}, length: {received_length}, content: \n{message_data.decode('ascii', errors='ignore')}")
                conn.sendall(b'OK')
                expected_packet_number += 1

if __name__ == "__main__":
    main()
