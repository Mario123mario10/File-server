# simple Python socket UDP server
# (C) Imie Naziwsko 2023 [PSI]

import socket
import sys
import struct
def is_printable_ascii(data):
    return all(32 <= byte <= 126 for byte in data)

if len(sys.argv) < 2:
    print("No port provided, using default 12345")
    PORT = 12345
else:
    PORT = int(sys.argv[1])

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
BUFSIZE = 512

print("Will listen on ", HOST, ":", PORT)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind((HOST, PORT))
    expected_packet_number = 0

    while True:
        data, addr = sock.recvfrom(BUFSIZE)
        if not data:
            print("Error in datagram?")
            break


        packet_number, data_length = struct.unpack('!Ih', data[:6])
        message_data = data[6:6+data_length]
        received_length = len(data)

#        received_length = int.from_bytes(data[4:6], byteorder="big")

        if packet_number != expected_packet_number:
            print("Missing packet! Expected {}, received {}".format(expected_packet_number, packet_number))

        elif received_length > BUFSIZE:
            print("Incorrect data length, bigger than buffer size. Got {}, BUFSIZE{}".format(received_length, BUFSIZE))

        elif received_length != data_length + 6:
            print("Incorrect data length. Expected {}, received {}".format(data_length + 6, received_length))

        elif not is_printable_ascii(message_data):
            print("Data is not printable ASCII")

        else:
            print("\nReceived packet # {}, length: {}, content: \n{}".format(packet_number, received_length, message_data.decode('ascii', errors='ignore')))
            sock.sendto(b'OK', addr)

            print('Sending confirmation for packet #', packet_number)

        expected_packet_number = packet_number + 1
