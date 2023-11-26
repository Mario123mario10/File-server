/* (c) Imie Nazwisko 2023 [PSI] */
#include "./udp_source_sink.h"
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

#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 12345
#define ASCII_START 32
#define ASCII_END 126

#define bailout(s) { perror(s); exit(1); }
#define Usage() { errx(0, "Usage: %s <host> <port> <count> <delay-s>\n", argv[0]); }

int main(int argc, char *argv[])
{
    int sock;
    struct sockaddr_in server;
    char buffer[DGRAMSIZE];
	char recv_buffer[DGRAMSIZE]; //bufor na odpowiedz (o takim samym rozmiarze jak datagram)
    int packet_number = 0;
    unsigned char current_char = ASCII_START;
	socklen_t addr_len = sizeof(server);

    if (argc != 5) Usage();

    /* Create socket. */
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == -1) bailout("Nie można utworzyć gniazda");

    /* Configure server. */
    server.sin_family = AF_INET;
    server.sin_port = htons(atoi(argv[2]));
    server.sin_addr.s_addr = inet_addr(argv[1]);

    while (packet_number < atoi(argv[3]))
    {
        int32_t packet_number_net = htonl(packet_number);
        int16_t data_length_net = htons(DGRAMSIZE - 6);

        memcpy(buffer, &packet_number_net, sizeof(packet_number_net));
        memcpy(buffer + sizeof(packet_number_net), &data_length_net, sizeof(data_length_net));

        for (int i = 6; i < DGRAMSIZE; i++)
		{
            buffer[i] = current_char;
            current_char++;
            if (current_char > ASCII_END) current_char = ASCII_START;
        }

		//Wyslanie datagramu
        if (sendto(sock, buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, sizeof(server)) < 0) perror("Nie można wysłać datagramu\n");
		
		// Odbieranie odpowiedzi
        if (recvfrom(sock, recv_buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, &addr_len) < 0) bailout("Błąd przy odbieraniu odpowiedzi");
        
        // Weryfikacja odpowiedzi
        if (strncmp(recv_buffer, "OK", 2) != 0) fprintf(stderr, "Otrzymano niepoprawną odpowiedź od serwera\n");
		else printf("Wysłano pakiet nr %d i otrzymano potwierdzenie\n", packet_number);//Wszystko poszlo OK
		
        packet_number++;
		sleep(atoi(argv[4])); 
    }

    close(sock);
    return 0;
}
