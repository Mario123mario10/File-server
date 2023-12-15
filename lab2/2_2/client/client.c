/* (c) Imie Nazwisko 2023 [PSI] */
#include <arpa/inet.h>
#include <err.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#define ASCII_START 32
#define ASCII_END 126
#define BSIZE 512

#define bailout(s) { perror(s); exit(1); }
#define Usage() { errx(0, "Usage: %s address-or-ip port count delay-ms\n", argv[0]); }

int main(int argc, char *argv[])
{
    int sock;
    struct sockaddr_in6 server;
    struct hostent *hp;
    char buffer[BSIZE];
    char recv_buffer[BSIZE];
    unsigned char current_char = ASCII_START;
    int packet_number, num_packets, delay_ms;

    if (argc != 5) Usage();

    sock = socket(AF_INET6, SOCK_STREAM, 0);
    if (sock == -1) bailout("opening stream socket");

    server.sin6_family = AF_INET6;
    hp = gethostbyname2(argv[1], AF_INET6);
    if (hp == NULL) errx(2, "%s: unknown host\n", argv[1]);


    memcpy(&server.sin6_addr, hp->h_addr, hp->h_length);
    server.sin6_port = htons(atoi(argv[2]));

    if (connect(sock, (struct sockaddr *) &server, sizeof(server)) == -1)
        bailout("connecting stream socket");

    num_packets = atoi(argv[3]);
    delay_ms = atoi(argv[4]);

    for (packet_number = 0; packet_number < num_packets; packet_number++)
    {
        int32_t packet_number_net = htonl(packet_number);
        int16_t data_length_net = htons(BSIZE - 6);
        memcpy(buffer, &packet_number_net, sizeof(packet_number_net));
        memcpy(buffer + sizeof(packet_number_net), &data_length_net, sizeof(data_length_net));

        for (int i = 6; i < BSIZE; i++) {
            buffer[i] = current_char;
            current_char++;
            if (current_char > ASCII_END) current_char = ASCII_START;
        }

        if (write(sock, buffer, BSIZE) == -1) bailout("writing on stream socket");

        // Odbiór i weryfikacja odpowiedzi od serwera
        if (read(sock, recv_buffer, BSIZE) == -1) bailout("reading from stream socket");

        // Wyświetlanie komunikatu o błędzie (jeśli wystąpił)
        if (strncmp(recv_buffer, "OK", 2) != 0) {
            printf("Received error response from server: %s\n", recv_buffer);
        } else {
            printf("Sent packet %d and received confirmation\n", packet_number);
        }

        usleep(delay_ms * 1000);  // opóźnienie
    }

    close(sock);
    return 0;
}
