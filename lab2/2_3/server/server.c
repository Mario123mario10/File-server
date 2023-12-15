#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <err.h>
#include <stdlib.h>

#define SLEEPFORMLSEC 1

void readNewPackage(char* buffer, int read_start, int* pckg_number, int* msg_size)
{
	int temp_pckg_number = 0;
	int temp_msg_size = 0;
	for (int i=0;i<4;i++)
	{
		temp_pckg_number = 256 * temp_pckg_number + (unsigned char) buffer[read_start + i];
	}
	for (int i=4;i<6;i++)
	{
		temp_msg_size = 256 * temp_msg_size + (unsigned char) buffer[read_start + i];
	}
	*pckg_number = temp_pckg_number;
	*msg_size = temp_msg_size;
}

void writeMessage(int pckgNumber, int pckgSize, char* pckgData)
{
	printf("package number - %i\n", pckgNumber);
	printf("package size - %i\n", pckgSize);
	printf("package data - %s\n", pckgData);
	// for (int i=0;i<pckgSize;i++)
	// {
	// 	printf("%c",(unsigned char) pckgData[i]);
	// }
}


int main(void)
{
	int buffer_size = 10*1024; //10 kb
	int read_buf_size = 512;
	int sock;
	struct sockaddr_in server;
	int msgsock;
	char buf[read_buf_size];
	char recvdmessage[buffer_size];
	int rval;

	int current_msg_size;
	int current_pckg_number;
	int current_buffer_end = 0;

	sock = socket(AF_INET, SOCK_STREAM, 0);
	if (sock == -1) {
		perror("opening stream socket");
		return 1;
	}

	server.sin_family = AF_INET;
	server.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
	//server.sin_addr.s_addr = INADDR_ANY;
	server.sin_port = 8080;
	if (bind(sock, (struct sockaddr*)&server, sizeof server) == -1)
		perror("binding stream socket");


	printf("Socket port: %d\n", ntohs(server.sin_port));

	listen(sock, 4);
	socklen_t addr_size = sizeof(struct sockaddr_in);
	msgsock = accept(sock, (struct sockaddr*)0, &addr_size);

	int has_read_header = 0;

	if (msgsock == -1) {
		perror("accept"); return 3;
	}
	else do {
		memset(buf, 0, sizeof buf);
		if ((rval = read(msgsock, buf, read_buf_size)) == -1) {
			perror("reading stream message");
			return 4;
		}
		if (rval == 0)
			printf("Ending connection\n");

		else
		{
			int data_to_parse = read_buf_size-6;
			int current_begin=0;

			if(!has_read_header)
			{
				readNewPackage(buf, 0, &current_pckg_number, &current_msg_size);
				has_read_header = 1;
				current_buffer_end = 0;
				current_begin += 6;
			}
			int temp = strlen(buf);
			data_to_parse = strlen(buf +current_begin);

			while(data_to_parse > 0)
			{
				int current_data_to_read;
				if(data_to_parse > current_msg_size - current_buffer_end)
				{
					data_to_parse -= current_msg_size - current_buffer_end;
					current_data_to_read = current_msg_size - current_buffer_end;
				}
				else
				{
					current_data_to_read = data_to_parse;
					data_to_parse = 0;
				}
				strncpy(&recvdmessage[current_buffer_end], &buf[current_begin], current_data_to_read);

				current_begin += current_data_to_read;
				current_buffer_end += current_data_to_read;

				if(current_buffer_end == current_msg_size){
					writeMessage(current_pckg_number, current_msg_size, recvdmessage);
					has_read_header = 0;
					current_buffer_end = 0;
					data_to_parse = strlen(buf +current_begin + 6);
					if(data_to_parse > 0) // if there is something after next header
					{
						readNewPackage(buf, current_begin, &current_pckg_number, &current_msg_size);
						has_read_header = 1;
						current_buffer_end = 0;
						current_begin += 6;
					}
					else if (data_to_parse == 0) continue;
					else
					{
						// there is currently no code to handle a situation
						// if stream buffer we receive, has the next package header split into the buffer
						// such a scenario is very unlikely to happen
						perror("incomplete data");
						return 5;
					}
				}
			}
			usleep(SLEEPFORMLSEC * 1000);
			current_begin = 0;
		}
	} while (rval > 0);
	close(msgsock);
	return 0;
}