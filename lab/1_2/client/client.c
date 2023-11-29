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
#include <sys/time.h>

#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 12345
#define ASCII_START 32
#define ASCII_END 126


#define BYTES_ADD 16
#define TIMEOUT 5

#define bailout(s) { perror(s); exit(1); }
#define Usage() { errx(0, "Usage: %s <host> <port> <delay-s>\n", argv[0]); }

int main(int argc, char *argv[])
{
    int sock;
    struct sockaddr_in server;
    struct hostent *hp;
    char buffer[DGRAMSIZE];
	char recv_buffer[DGRAMSIZE]; //bufor na odpowiedz (o takim samym rozmiarze jak datagram)
    int packet_number = 0;
    unsigned char current_char = ASCII_START;
	socklen_t addr_len = sizeof(server);

    setvbuf(stdout, NULL, _IONBF, 0);

    if (argc != 4) Usage();

    /* Create socket. */
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == -1) bailout("Nie można utworzyć gniazda");

    /* Configure server. */
    /* uzyskajmy adres IP z nazwy . */
    server.sin_family = AF_INET;
    hp = gethostbyname2(argv[1], AF_INET);

    /* hostbyname zwraca strukture zawierajaca adres danego hosta */
    if (hp == (struct hostent *) 0) errx(2, "%s: unknown host\n", argv[1]);
    printf("address resolved...\n");
	
	memcpy((char *) &server.sin_addr, (char *) hp->h_addr, hp->h_length);
    server.sin_port = htons(atoi(argv[2]));

    char *ip = inet_ntoa(server.sin_addr);

    printf("Resolved IP: ");
    printf(ip);
    printf("\n");

    struct timeval tv;
    tv.tv_sec = 4;
    tv.tv_usec = 0;
    if (setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO,&tv,sizeof(tv)) < 0) {
        perror("Error");
    }

    int cur_size = 0;
    while (1)
    {
        cur_size += BYTES_ADD;
        buffer[cur_size];
        int32_t packet_number_net = htonl(packet_number);
        int16_t data_length_net = htons(cur_size-6);

        memcpy(buffer, &packet_number_net, sizeof(packet_number_net));
        memcpy(buffer + sizeof(packet_number_net), &data_length_net, sizeof(data_length_net));

        int i;
        for (i = 6; i < DGRAMSIZE; i++)
		{
            buffer[i] = current_char;
            current_char++;
            if (current_char > ASCII_END) current_char = ASCII_START;
        }

		//Wyslanie datagramu
        if (sendto(sock, buffer, cur_size, 0, (struct sockaddr *)&server, sizeof(server)) < 0) perror("Nie można wysłać datagramu\n");

		// Odbieranie odpowiedzi
        if (recvfrom(sock, recv_buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, &addr_len) < 0) bailout("Brak potwierdzenia od serwera\n");


        // Weryfikacja odpowiedzi
        if (strncmp(recv_buffer, "OK", 2) != 0) fprintf(stderr, "Otrzymano niepoprawną odpowiedź od serwera\n");
		else printf("Wysłano pakiet nr %d o wielkości %d i otrzymano potwierdzenie\n", packet_number, cur_size);//Wszystko poszlo OK

        packet_number++;
		sleep(atoi(argv[3]));
    }

    close(sock);
    return 0;
}