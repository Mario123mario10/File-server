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

#define ASCII_START 32
#define ASCII_END 126

#define bailout(s) { perror(s); exit(1); }
#define Usage() { errx(0, "Usage: %s <host> <port> <count> <delay-in-ms>\n", argv[0]); }

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
	long int i, udelay;
	
    if (argc != 5) Usage();
	udelay = atol(argv[4]) * 1000; //Opoznienie w mikrosekundach

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
	
	connect (sock, (struct sockaddr *) &server, sizeof(server) );
	
	for (packet_number = 0; packet_number < atoi(argv[3]); ++packet_number)
    {
		usleep(udelay);

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
		if (sendto(sock, buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, sizeof(server)) < 0)
		{
			perror("Nie można wysłać datagramu\n");
			continue;
		}
		
		// Odbieranie odpowiedzi
		if (recvfrom(sock, recv_buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, &addr_len) < 0)
		{
			perror("Błąd przy odbieraniu odpowiedzi\n");
			continue;
		}
        
        // Weryfikacja odpowiedzi
		if (strncmp(recv_buffer, "OK", 2) != 0)
		{
			perror("Otrzymano niepoprawną odpowiedź od serwera\n");
			continue;
		}
		printf("Wysłano pakiet nr %d i otrzymano potwierdzenie\n", packet_number); //Wszystko poszlo OK
    }

    close(sock);
    return 0;
}
