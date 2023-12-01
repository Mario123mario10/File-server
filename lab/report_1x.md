# PSI 23Z Lab - Sprawozdanie z zadań 1.x

Zespół 21 w składzie:

- Damian Pałyska
- Michał Bogiel
- Mariusz Pakulski
- Jan Kowalczewski

Data: w nagłówku
Wersja 1.

## Polecenie (wariant Aa)

Zadanie 1 Komunikacja UDP

Napisz zestaw dwóch programów – klienta i serwera wysyłające datagramy UDP. Wykonaj ćwiczenie w kolejnych inkrementalnych wariantach (rozszerzając kod z poprzedniej wersji).

## Platforma testowa

Do testów wykorzystujemy kontenery Docker uruchamiane przez plik docker-compose.
W każdym zadaniu występują dwa kontenery:

- Kontener z_21_1x_client dla klienta bazujący na gcc w wersji 4.9
- Kontener z_21_1x_server dla serwera bazujący na obrazie python w wersji 3

Kontenery komunikują się między sobą w sieci z21_network, czyli 172.21.21.0/24.

Wszystkie testy uruchamiane były na serwerze bigubu.ii.pw.edu.pl i stamtąd pochodzą wszystkie wydruki.

<div style="page-break-after: always;"></div>

## Zadanie 1.1

### Polecenie

Klient wysyła, a serwer odbiera datagramy o stałym rozmiarze (rzędu kilkuset bajtów).
Datagramy powinny posiadać ustaloną format danych: pierwsze cztery bajty zawierają numer kolejny pakietu (liczony od 0, typ int32), kolejne dwa bajty datagramu powinny zawierać informację o jego długości (typ int16), a kolejne bajty to kolejne [drukowalne znaki](https://en.wikipedia.org/wiki/ASCII#Printable_characters) powtarzające się wymaganą liczbę razy, aby osiągnąć zakładany rozmiar.
Odbiorca powinien weryfikować odebrany datagram i odsyłać odpowiedź (potwierdzenie) o ustalonym formacie. Serwer powinien sygnalizować brak pakietu (przeskok w numeracji pakietu).
Może być pomocne użycie pakietu struct w Python do konstrukcji i odbierania danych w zadanym
formacie.

Klient w C, serwer w Python.

Można także napisać wersje klienta i serwera w obu językach, ale muszą ze sobą współpracować. Należy zwrócić uwagę na rozmiary danych odczytanych z funkcji sieciowych i weryfikować z rozmiarem przesłanym w „nagłówku” danych. Sygnalizować rozbieżność.

### Opis rozwiązania

Klient (C)

```c
/* Create socket. */
sock = socket(AF_INET, SOCK_DGRAM, 0);
if (sock == -1) bailout("Cannot create socket");

/* Configure server. */
/* get IP address from name */
server.sin_family = AF_INET;
hp = gethostbyname2(argv[1], AF_INET);

/* hostbyname returns a structure containing host's address */
if (hp == (struct hostent *) 0) errx(2, "%s: unknown host\n", argv[1]);
printf("address resolved...\n");

memcpy((char *) &server.sin_addr, (char *) hp->h_addr, hp->h_length);
server.sin_port = htons(atoi(argv[2]));

char *ip = inet_ntoa(server.sin_addr);

printf("Resolved IP: ");
printf(ip);
printf("\n");

connect (sock, (struct sockaddr *) &server, sizeof(server) );

for (packet_number = 0; packet_number < atoi(argv[3]); ++packet_number)
{
    usleep(udelay);

    int32_t packet_number_net = htonl(packet_number);
    int16_t data_length_net = htons(DGRAMSIZE - 6);

    memcpy(buffer, &packet_number_net, sizeof(packet_number_net));
    memcpy(buffer + sizeof(packet_number_net), &data_length_net, sizeof(data_length_net));

    int i;
    for (i = 6; i < DGRAMSIZE; i++)
    {
        buffer[i] = current_char;
        current_char++;
        if (current_char > ASCII_END) current_char = ASCII_START;
    }

    // Sending datagram
    if (sendto(sock, buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, sizeof(server)) < 0)
    {
        perror("Cannot send datagram\n");
        continue;
    }

    // Receiving response
    if (recvfrom(sock, recv_buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, &addr_len) < 0)
    {
        perror("Error in receiving response\n");
        continue;
    }

    // Response verification
    if (strncmp(recv_buffer, "OK", 2) != 0)
    {
        perror("Received incorrect response from server\n");
        continue;
    }
    printf("Sent packet %d and received confirmation\n", packet_number); // Everything went OK
}

close(sock);
```

Klient tworzy gniazdo i konfiguruje połączenie z serwerem. W głównej pętli tworzy datagramy UDP zawierające:

- Kolejny numer pakietu (4 bajty, int32; jest on później inkrementowany),
- Długość datagramu (2 bajty, int16).
- Dane w postaci drukowalnych znaków ASCII. Klient wysyła te datagramy do serwera i oczekuje na potwierdzenie odbioru.

Każdy pakiet zostaje wysłany za pomocą systemowej funkcji sendto. Następnie czeka na potwierdzenie weryfikacji od serwera (recvfrom). Weryfikuje potwierdzenie, aby sprawdzić czy wszystko jest ok. (porównanie napisów za pomocą strncmp). Następnie inkrementuje numer następnego pakietu, zasypia na chwilę i kontynuuje działanie od nowa.

Serwer (Python)

```python
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.bind((HOST, PORT))
    packet_number = -1

    while True:
        data, addr = sock.recvfrom(BUFSIZE)
        if not data:
            print("Error in datagram?")
            break

        expected_packet_number = packet_number + 1

        packet_number, data_length = struct.unpack('!Ih', data[:6])
        message_data = data[6:6+data_length]
        received_length = len(data)

        if packet_number != expected_packet_number:
            print("Missing packet! Expected {}, received {}".format(expected_packet_number, packet_number))
            sock.sendto(b'Missing packet', addr)
            continue

        if received_length != data_length + 6:
            print("Incorrect data length. Expected {}, received {}".format(data_length + 6, received_length))
            sock.sendto(b'Incorrect data length', addr)
            continue

        if not is_printable_ascii(message_data):
            print("Data is not printable ASCII")
            sock.sendto(b'Data is not printable ASCII', addr)
            continue

        print("\nReceived packet # {}, length: {}, content: \n{}".format(packet_number, received_length, message_data.decode('ascii', errors='ignore')))

        sock.sendto(b'OK', addr)
        print('Sending confirmation for packet #', packet_number)
```

Serwer tworzy gniazdo i nasłuchuje na określonym porcie. Odbiera datagramy (sock.recvfrom) i sprawdza ich poprawność pod kątem:

- Numeru kolejnego pakietu (dla wykrycia ewentualnych utrat pakietów).
- Długości danych (porównanie z deklarowaną długością w datagramie).
- Poprawności danych (czy są drukowalnymi znakami ASCII – is_printable_ascii). Serwer odsyła potwierdzenie odbioru do klienta po każdym otrzymanym datagramie. (sendto)

Po każdym odebranym pakiecie, inkrementuje oczekiwany numer pakietu.

### Testowanie

Testowanie polegało na uruchomieniu serwera i klienta, a następnie obserwowaniu logów serwera podczas odbierania i przetwarzania datagramów.

```text
z21_11_server  | Will listen on  0.0.0.0 : 8888
z21_11_client  | address resolved...
z21_11_client  | Resolved IP: 172.21.21.2
z21_11_client  | Sent packet 0 and received confirmation
z21_11_server  |
z21_11_server  | Received packet # 0, length: 512, content:
z21_11_server  |  !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>
z21_11_server  | Sending confirmation for packet # 0
z21_11_server  |
z21_11_server  |
z21_11_server  | Received packet # 1, length: 512, content:
z21_11_server  | ?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]
z21_11_server  | Sending confirmation for packet # 1
z21_11_server  |
z21_11_client  | Sent packet 1 and received confirmation
z21_11_server  |
z21_11_server  | Received packet # 2, length: 512, content:
z21_11_server  | ^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|
z21_11_server  | Sending confirmation for packet # 2
z21_11_server  |
z21_11_client  | Sent packet 2 and received confirmation
z21_11_client  | Sent packet 3 and received confirmation
z21_11_server  |
z21_11_server  | Received packet # 3, length: 512, content:
z21_11_server  | }~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<
z21_11_server  | Sending confirmation for packet # 3
z21_11_server  |
z21_11_client  | Sent packet 4 and received confirmation
z21_11_server  |
z21_11_server  | Received packet # 4, length: 512, content:
z21_11_server  | =>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[
z21_11_server  | Sending confirmation for packet # 4
z21_11_server  |
z21_11_client  | Sent packet 5 and received confirmation
z21_11_server  |
z21_11_server  | Received packet # 5, length: 512, content:
z21_11_server  | \]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz
z21_11_server  | Sending confirmation for packet # 5
z21_11_server  |
z21_11_server  |
z21_11_server  | Received packet # 6, length: 512, content:
z21_11_server  | {|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:
z21_11_server  | Sending confirmation for packet # 6
z21_11_server  |
z21_11_client  | Sent packet 6 and received confirmation
z21_11_client  | Sent packet 7 and received confirmation
z21_11_server  |
z21_11_server  | Received packet # 7, length: 512, content:
z21_11_server  | ;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXY
z21_11_server  | Sending confirmation for packet # 7
z21_11_server  |
z21_11_server  |
z21_11_server  | Received packet # 8, length: 512, content:
z21_11_server  | Z[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwx
z21_11_server  | Sending confirmation for packet # 8
z21_11_server  |
z21_11_client  | Sent packet 8 and received confirmation
z21_11_server  |
z21_11_server  | Received packet # 9, length: 512, content:
z21_11_server  | yz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./012345678
z21_11_server  | Sending confirmation for packet # 9
z21_11_server  |
z21_11_client  | Sent packet 9 and received confirmation
z21_11_client exited with code 0
```

### Uwagi dot. problemów

Największym wyzwaniem było zapewnienie poprawnej komunikacji między klientem a serwerem, szczególnie przy weryfikacji poprawności otrzymanych danych. Problem ten rozwiązano poprzez dodanie szczegółowej weryfikacji danych w serwerze. Istotne okazało się także odwracanie kolejności bajtów w „nagłówku”, za pomocą funkcji htons i htonl – ze względu na konieczność konwersji ze standardu hosta na standard sieciowy (używany do transmisji danych).

<div style="page-break-after: always;"></div>

## Zadanie 1.2

### Polecenie

Na bazie kodu z zadania 1.1 napisać klienta, który wysyła kolejne datagramy o przyrastającej wielkości o np. 256 bajtów. Sprawdzić, jaki był maksymalny rozmiar wysłanego (przyjętego) datagramu. Zaproponować algorytm (niekoniecznie implementować) takiego sterowania rozmiarem pakietów, aby jak najszybciej ustalić ten rozmiar z dokładnością do jednego bajta. Po tym zakończyć program klienta. Wyjaśnić.

To zadanie można wykonać, korzystając z kodu klienta i serwera napisanych w C lub w Pythonie (tak jak wskazano w zadaniu 1.1). Nie trzeba tworzyć wersji w obydwu językach.

### Opis rozwiązania

Kod w zadaniu to jest zmodyfikowany kod z zadania 1.1. Tak więc nie będzie cały pokazany

Klient c
```c

#define BYTES_ADD 16

//...

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
    char buffer[cur_size];
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

    // Sending datagram
    if (sendto(sock, buffer, cur_size, 0, (struct sockaddr *)&server, sizeof(server)) < 0) perror("Cannot send datagram\n");

    // Receiving response
    if (recvfrom(sock, recv_buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, &addr_len) < 0) bailout("No response from server\n");


    // Response verification
    if (strncmp(recv_buffer, "OK", 2) != 0) fprintf(stderr, "Received incorrect response from server\n");
    else printf("Sent packet %d of size %d and received confirmation\n", packet_number, cur_size); // Everything went OK

    packet_number++;
    sleep(atoi(argv[3]));
}
```
Zmiany: Tworzona jest zmienna buffer o zmiennej wielkości, oraz struktura timeval określająca długość czasu nasłuchiwania.
Jeśli serwer otrzyma dane o odpowiedniej długości, odsyła do klienta komunikat. Jeśli danych w datagramie będzie więcej niż przewidziano po stronie serwera, serwer nie odpowie, a klient po określonym czasie zerwie połączenie.
klient python
```python
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
```
Jeśli serwer otrzyma za dużo danych, wyświetla odpowiedni komunikat

### Proponowany Algorytm
1.0 ustalamy wartości początkowe, rozmiar (wiadomości) = 512 \
1.1 rozmiar *= 2 \
1.2 spróbuj wysłać \
1.3 jeśli się udało powróć do 1.1 \
2.0 potega2 = rozmiar \
2.1 potega2 = potega2 / 2 \
2.2 maxrozzmiar += potega2 \
2.3 jeśli udało się przesłać  powrót do 2.1 \
2.4 jeśłi nie maxrozmiar -= potega2 \
2.5 Powrót do 2.1

### Testowanie

```text
z21_12_server  | Will listen on  0.0.0.0 : 8888
z21_12_client  | address resolved...
z21_12_client  | Resolved IP: 172.21.21.2
z21_12_server  |
z21_12_server  | Received packet # 0, length: 16, content:
z21_12_server  |  !"#$%&'()
z21_12_server  |
z21_12_client  | Sent packet 0 of size 16 and received confirmation
z21_12_server  | Sending confirmation for packet # 0
z21_12_server  |
z21_12_server  | Received packet # 1, length: 32, content:
z21_12_server  | ?@ABCDEFGHIJKLMNOPQRSTUVWX
z21_12_server  | Sending confirmation for packet # 1
z21_12_server  |
z21_12_client  | Sent packet 1 of size 32 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 2, length: 48, content:
z21_12_server  | ^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'(
z21_12_server  |
z21_12_server  | Sending confirmation for packet # 2
z21_12_client  | Sent packet 2 of size 48 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 3, length: 64, content:
z21_12_server  | }~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVW
z21_12_server  | Sending confirmation for packet # 3
z21_12_server  |
z21_12_client  | Sent packet 3 of size 64 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 4, length: 80, content:
z21_12_server  | =>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'
z21_12_server  | Sending confirmation for packet # 4
z21_12_server  |
z21_12_client  | Sent packet 4 of size 80 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 5, length: 96, content:
z21_12_server  | \]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUV
z21_12_server  |
z21_12_server  | Sending confirmation for packet # 5
z21_12_client  | Sent packet 5 of size 96 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 6, length: 112, content:
z21_12_server  | {|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&
z21_12_server  |
z21_12_server  | Sending confirmation for packet # 6
z21_12_client  | Sent packet 6 of size 112 and received confirmation
z21_12_client  | Sent packet 7 of size 128 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 7, length: 128, content:
z21_12_server  | ;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTU
z21_12_server  | Sending confirmation for packet # 7
z21_12_server  |
z21_12_server  |
z21_12_server  | Received packet # 8, length: 144, content:
z21_12_server  | Z[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%
z21_12_server  | Sending confirmation for packet # 8
z21_12_server  |
z21_12_client  | Sent packet 8 of size 144 and received confirmation
z21_12_client  | Sent packet 9 of size 160 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 9, length: 160, content:
z21_12_server  | yz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRST
z21_12_server  | Sending confirmation for packet # 9
z21_12_server  |
z21_12_client  | Sent packet 10 of size 176 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 10, length: 176, content:
z21_12_server  | 9:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$
z21_12_server  | Sending confirmation for packet # 10
z21_12_server  |
z21_12_client  | Sent packet 11 of size 192 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 11, length: 192, content:
z21_12_server  | XYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRS
z21_12_server  | Sending confirmation for packet # 11
z21_12_server  |
z21_12_client  | Sent packet 12 of size 208 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 12, length: 208, content:
z21_12_server  | wxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#
z21_12_server  | Sending confirmation for packet # 12
z21_12_server  |
z21_12_server  |
z21_12_server  | Received packet # 13, length: 224, content:
z21_12_server  | 789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQR
z21_12_server  |
z21_12_server  | Sending confirmation for packet # 13
z21_12_client  | Sent packet 13 of size 224 and received confirmation
z21_12_client  | Sent packet 14 of size 240 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 14, length: 240, content:
z21_12_server  | VWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"
z21_12_server  | Sending confirmation for packet # 14
z21_12_server  |
z21_12_client  | Sent packet 15 of size 256 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 15, length: 256, content:
z21_12_server  | uvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQ
z21_12_server  | Sending confirmation for packet # 15
z21_12_server  |
z21_12_server  |
z21_12_server  | Received packet # 16, length: 272, content:
z21_12_server  | 56789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !
z21_12_server  | Sending confirmation for packet # 16
z21_12_server  |
z21_12_client  | Sent packet 16 of size 272 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 17, length: 288, content:
z21_12_server  | TUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOP
z21_12_server  | Sending confirmation for packet # 17
z21_12_server  |
z21_12_client  | Sent packet 17 of size 288 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 18, length: 304, content:
z21_12_server  | stuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~
z21_12_server  |
z21_12_server  | Sending confirmation for packet # 18
z21_12_client  | Sent packet 18 of size 304 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 19, length: 320, content:
z21_12_server  | 3456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNO
z21_12_server  | Sending confirmation for packet # 19
z21_12_server  |
z21_12_client  | Sent packet 19 of size 320 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 20, length: 336, content:
z21_12_server  | RSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~
z21_12_server  | Sending confirmation for packet # 20
z21_12_server  |
z21_12_client  | Sent packet 20 of size 336 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 21, length: 352, content:
z21_12_server  | qrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMN
z21_12_server  | Sending confirmation for packet # 21
z21_12_server  |
z21_12_client  | Sent packet 21 of size 352 and received confirmation
z21_12_client  | Sent packet 22 of size 368 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 22, length: 368, content:
z21_12_server  | 123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}
z21_12_server  | Sending confirmation for packet # 22
z21_12_server  |
z21_12_server  |
z21_12_server  | Received packet # 23, length: 384, content:
z21_12_server  | PQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLM
z21_12_server  | Sending confirmation for packet # 23
z21_12_server  |
z21_12_client  | Sent packet 23 of size 384 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 24, length: 400, content:
z21_12_server  | opqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|
z21_12_server  | Sending confirmation for packet # 24
z21_12_server  |
z21_12_client  | Sent packet 24 of size 400 and received confirmation
z21_12_client  | Sent packet 25 of size 416 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 25, length: 416, content:
z21_12_server  | /0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKL
z21_12_server  |
z21_12_server  | Sending confirmation for packet # 25
z21_12_client  | Sent packet 26 of size 432 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 26, length: 432, content:
z21_12_server  | NOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{
z21_12_server  | Sending confirmation for packet # 26
z21_12_server  |
z21_12_client  | Sent packet 27 of size 448 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 27, length: 448, content:
z21_12_server  | mnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJK
z21_12_server  | Sending confirmation for packet # 27
z21_12_server  |
z21_12_client  | Sent packet 28 of size 464 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 28, length: 464, content:
z21_12_server  | -./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz
z21_12_server  | Sending confirmation for packet # 28
z21_12_server  |
z21_12_server  |
z21_12_server  | Received packet # 29, length: 480, content:
z21_12_server  | LMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJ
z21_12_server  | Sending confirmation for packet # 29
z21_12_server  |
z21_12_client  | Sent packet 29 of size 480 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 30, length: 496, content:
z21_12_server  | klmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxy
z21_12_server  | Sending confirmation for packet # 30
z21_12_server  |
z21_12_client  | Sent packet 30 of size 496 and received confirmation
z21_12_client  | Sent packet 31 of size 512 and received confirmation
z21_12_server  |
z21_12_server  | Received packet # 31, length: 512, content:
z21_12_server  | +,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHI
z21_12_server  | Sending confirmation for packet # 31
z21_12_server  |
z21_12_server  | Incorrect data length. Expected 528, received 512
z21_12_client exited with code 1

```
### Wnioski

Zadanie wymagało zmodyfikowanie działana serwera jak i klienta.  W kliencie tym zmodyfikowaniem było dodaje timeouta, alternatywną wersją mogłoby być zmodyfikowanie kodu, aby serwer zawsze wysyłał odpowiedź, tylko ta odpowiedź różniła by się w zależności od liczby bajtów przesłanych przez klienta.

<div style="page-break-after: always;"></div>

## Zadanie 1.3

### Polecenie

Uruchomić program z przykładu 1.1 w środowisku symulującym błędy gubienia pakietów. (Informacja o tym jak to zrobić znajduje się w skrypcie opisującym środowisko Dockera). Rozszerzyć protokół i program tak, aby gubione pakiety były wykrywane i retransmitowane.

### Opis rozwiązania

Wykrycie i retransmisję pakietu zapewniono poprzez ustawienie maksymalnego czasu czekania na potwierdzenie (opcja gniazda):

```c
struct timeval tv;
tv.tv_sec = 4;
tv.tv_usec = 0;
if (setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO,&tv,sizeof(tv)) < 0) {
    perror("Error");
}
```

Oraz wysyłanie pakietu w pętli, aż do uzyskania potwierdzenia.

```c
int sendMessage(int sock, char* buffer[], char* recv_buffer[], struct sockaddr_in server) {
    socklen_t addr_len = sizeof(server);

    // Sending datagram
    if (sendto(sock, buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, addr_len) < 0)
    {
        perror("Cannot send datagram\n");
        return -1;
    }

    // Receiving response
    if (recvfrom(sock, recv_buffer, DGRAMSIZE, 0, (struct sockaddr *)&server, &addr_len) < 0)
    {
        printf("Sending datagram again\n");
        return sendMessage(sock, buffer, recv_buffer, server);
    }
    return 1;
}
```

W kodzie serwera zmienie uległ jedynie fragment sprawdzania numeru pakietu:
```
    if packet_number != expected_packet_number and packet_number != expected_packet_number-1:
            print("Missing packet! Expected {}, received {}".format(expected_packet_number, packet_number))
            sock.sendto(b'Missing packet', addr)
            continue
```


### Testowanie

W stosunku do testowania w zadaniu 1.1 dodatkowo trzeba było skonfigurować symulację gubienia pakietów poprzez wywołanie polecenia w odpowiednim kontenerze.

```text
z21_13_client  | address resolved...
z21_13_client  | Resolved IP: 172.21.21.2
z21_13_server  | Missing packet! Expected 10, received 0
z21_13_client  | Received incorrect response from server
z21_13_client  | : Success
z21_13_server  |
z21_13_server  | Received packet # 1, length: 512, content:
z21_13_server  | ?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]
z21_13_server  | Sending confirmation for packet # 1
z21_13_server  |
z21_13_client  | Sent packet 1 and received confirmation
z21_13_server  |
z21_13_server  | Received packet # 2, length: 512, content:
z21_13_server  | ^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|
z21_13_server  | Sending confirmation for packet # 2
z21_13_server  |
z21_13_client  | Sent packet 2 and received confirmation
z21_13_server  |
z21_13_server  | Received packet # 3, length: 512, content:
z21_13_server  | }~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<
z21_13_server  | Sending confirmation for packet # 3
z21_13_server  |
z21_13_client  | Sent packet 3 and received confirmation
z21_13_server  |
z21_13_server  | Received packet # 4, length: 512, content:
z21_13_server  | =>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[
z21_13_server  |
z21_13_server  | Sending confirmation for packet # 4
z21_13_client  | Sent packet 4 and received confirmation
z21_13_server  |
z21_13_server  | Received packet # 5, length: 512, content:
z21_13_server  | \]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz
z21_13_server  | Sending confirmation for packet # 5
z21_13_server  |
z21_13_client  | Sent packet 5 and received confirmation
```

Do tej pory komunikacja wygląda identycznie jak w zadaniu 1.1.
W tym momencie zostaje wywołana komenda `docker exec z21_13_client tc qdisc add dev eth0 root netem delay 1000ms 500ms loss 50%`

```text
z21_13_client  | Sending datagram again
z21_13_server  |
z21_13_server  | Received packet # 6, length: 512, content:
z21_13_server  | {|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:
z21_13_server  | Sending confirmation for packet # 6
z21_13_server  |
z21_13_client  | Sent packet 6 and received confirmation
z21_13_client  | Sending datagram again
z21_13_client  | Sending datagram again
z21_13_server  |
z21_13_server  | Received packet # 7, length: 512, content:
z21_13_server  | ;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXY
z21_13_server  | Sending confirmation for packet # 7
z21_13_server  |
z21_13_client  | Sent packet 7 and received confirmation
z21_13_client  | Sending datagram again
z21_13_server  |
z21_13_server  | Received packet # 8, length: 512, content:
z21_13_server  | Z[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwx
z21_13_server  | Sending confirmation for packet # 8
z21_13_server  |
z21_13_client  | Sent packet 8 and received confirmation
z21_13_client  | Sending datagram again
z21_13_server  |
z21_13_server  | Received packet # 9, length: 512, content:
z21_13_server  | yz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./012345678
z21_13_server  | Sending confirmation for packet # 9
z21_13_server  |
z21_13_client  | Sent packet 9 and received confirmation
z21_13_client exited with code
```

Mechanizm zapobiegania gubieniu pakietów działa prawidłowo - w obu przybadkach zgbubienie pakietu wysłanego przez klienta jak i zgubieniu pakietu przez serwer.
Jeśli zgubiony zostanie pakiet wysłany przez klienta, serwer nie dostanie żadnej informacji więc nie wyśle  potwierdzenia ani nie zwiekszy numeru oczekiwanego pakietu. W tej sytuacji pakiet wysyłany jest ponownie.
Jeśli zgubiony zostanie pakiet wysłany przez serewer(potwierdzenie) , serwer dokona zwiekszenia numeru oczekiwanego pakietu. W tej sytuacji pakiet wysyłany jest ponownie a serwer uznaje to sytuacje za prawidłową nie zmienia licznika spodziewanego pakietu i ponownie wysyła potwierdzenie .
## Wnioski

Projekt pokazał praktyczne zastosowanie protokołów UDP w komunikacji sieciowej. Zostały poruszone kluczowe aspekty programowania sieciowego, takie jak obsługa datagramów, weryfikacja danych i obsługa błędów.
