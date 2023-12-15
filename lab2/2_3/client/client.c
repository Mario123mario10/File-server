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
#include <time.h>
#include <sys/time.h>

#define ASCII_START 32
#define ASCII_END 126

#define bailout(s) { perror(s); exit(1); }
#define Usage() { errx(0, "Usage: %s address-or-ip port count number-of-packets-in-a-bucket buffer-size\n", argv[0]); }

int main(int argc, char *argv[])
{
    if (argc != 6) Usage();

    int buffer_size = atoi(argv[5]);

    struct timeval stop, start;
    gettimeofday(&stop, NULL);
    int sock;
    struct sockaddr_in server;
    struct hostent *hp;
    char buffer[buffer_size];
    char recv_buffer[buffer_size];
    unsigned char current_char = ASCII_START;
    int packet_number, num_packets, average_of;


    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == -1) bailout("opening stream socket");

    server.sin_family = AF_INET;
    hp = gethostbyname(argv[1]);
    if (hp == NULL) errx(2, "%s: unknown host\n", argv[1]);

    memcpy(&server.sin_addr, hp->h_addr, hp->h_length);
    server.sin_port = htons(atoi(argv[2]));

    if (connect(sock, (struct sockaddr *) &server, sizeof(server)) == -1)
        bailout("connecting stream socket");

    num_packets = atoi(argv[3]);
    average_of = atoi(argv[4]);


    long sendingTime[num_packets];

    for (packet_number = 0; packet_number < num_packets; packet_number++)
    {
        int32_t packet_number_net = htonl(packet_number);
        int16_t data_length_net = htons(buffer_size - 6);
        memcpy(buffer, &packet_number_net, sizeof(packet_number_net));
        memcpy(buffer + sizeof(packet_number_net), &data_length_net, sizeof(data_length_net));

        for (int i = 6; i < buffer_size; i++) {
            buffer[i] = current_char;
            current_char++;
            if (current_char > ASCII_END) current_char = ASCII_START;
        }
        //buffer[buffer_size-1] = 0;
        gettimeofday(&start, NULL);
        if (write(sock, buffer, buffer_size) == -1) bailout("writing on stream socket");
        gettimeofday(&stop, NULL);
        sendingTime[packet_number] = 1000000*(stop.tv_sec-start.tv_sec) + (stop.tv_usec-start.tv_usec);
    }

    long long time = 0;
    int i_begin = 0;
    for(int i = 0; i < num_packets; i++)
    {
        time += sendingTime[i];
        if(i % average_of == 0)
        {
            if(i == 0) continue; // prevent first empty print
                printf("average time in microseconds: %llu, between packages %d and %d \n", (time /average_of), i_begin, i);
            i_begin = i;
            time = 0;
        }
    }

    printf("average time in microseconds: %llu, between packages %d and %d \n", (time /average_of), i_begin, num_packets);
    close(sock);
    return 0;
}
