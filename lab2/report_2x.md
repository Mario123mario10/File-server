# PSI 23Z Lab - Sprawozdanie z zadań 2.x

Zespół 21 w składzie:

- Damian Pałyska
- Michał Bogiel
- Mariusz Pakulski
- Jan Kowalczewski

Data: w nagłówku
Wersja 1.

## Polecenie (wariant 2.3a)

Zadanie 2 Komunikacja TCP

Napisz zestaw dwóch programów – klienta i serwera komunikujących się poprzez TCP. Wykonaj
ćwiczenie w kolejnych inkrementalnych wariantach (rozszerzając kod z poprzedniej wersji).

## Platforma testowa

Do testów wykorzystujemy kontenery Docker uruchamiane przez plik docker-compose.
W każdym zadaniu występują dwa kontenery:

- Kontener z_21_2x_client dla klienta bazujący na gcc w wersji 4.9
- Kontener z_21_2x_server dla serwera bazujący na obrazie python w wersji 3

Kontenery komunikują się między sobą w sieci z21_network, czyli `172.21.21.0/24` (IPv4) lub `fd00:1032:ac21:21::/64` (IPv6).

Wszystkie testy uruchamiane były na serwerze bigubu.ii.pw.edu.pl i stamtąd pochodzą wszystkie wydruki.

<div style="page-break-after: always;"></div>

## Zadanie 2.1

### Polecenie

Napisz w języku C/Python klienta TCP, który wysyła „złożoną” strukturę danych, taką jaką
przydzielono w zadaniu 1.1 (Warianty A,B,C lub D). Serwer napisany w Pythonie/C powinien te
dane odebrać, dokonać poprawnego „odpakowania” tej struktury i wydrukować jej pola (być może
w skróconej postaci, aby uniknąć nadmiaru wyświetlanych danych). Klient oraz serwer powinny
być napisane w różnych językach.
Wskazówka: można wykorzystać moduły Python-a: struct i io.
 
Klient w C, serwer w Python.

### Opis rozwiązania

Opis rozwiązania
Klient (C)
	
```c
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
delay_ms = atoi(argv[4]);

for (packet_number = 0; packet_number < num_packets; packet_number++)
{
    int32_t packet_number_net = htonl(packet_number);
    int16_t data_length_net = htons(BSIZE - 6);
    memcpy(buffer, &packet_number_net, sizeof(packet_number_net));
    memcpy(buffer + sizeof(packet_number_net), &data_length_net, sizeof(data_length_net));

    for (int i = 6; i < BSIZE; i++) 
    {
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
```

Klient tworzy gniazdo oraz konfiguruje i nawiązuje połączenie z serwerem (za pomocą funkcji connect). W głównej pętli tworzy datagramy zawierające:

- Kolejny numer pakietu (4 bajty, int32; jest on później inkrementowany),
- Długość datagramu (2 bajty, int16).
- Dane w postaci drukowalnych znaków ASCII. Klient wysyła te datagramy do serwera i oczekuje na potwierdzenie odbioru.

Każdy pakiet zostaje wysłany za pomocą systemowej funkcji sendto. Następnie czeka na potwierdzenie weryfikacji od serwera (recvfrom). Weryfikuje potwierdzenie, aby sprawdzić czy wszystko jest ok. (porównanie napisów za pomocą strncmp). Następnie inkrementuje numer następnego pakietu, zasypia na chwilę i kontynuuje działanie od nowa.

Serwer (Python)

```python
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
```

Serwer tworzy gniazdo powiązane z określonym hostem i portem (metoda bind) i nasłuchuje (listen), oczekując na nawiązanie połączenia (accept – ta metoda zwraca połączenie i adres) . Odbiera datagramy (conn.recv) i sprawdza ich poprawność pod kątem:

- Numeru kolejnego pakietu (dla wykrycia ewentualnych utrat pakietów).
- Długości danych (porównanie z deklarowaną długością w datagramie).
- Poprawności danych (czy są drukowalnymi znakami ASCII – is_printable_ascii). Serwer odsyła potwierdzenie odbioru do klienta po każdym otrzymanym datagramie. (sendto)

Po każdym otrzymanym datagramie, jeśli wszystko się zgadza, serwer odsyła potwierdzenie odbioru do klienta (i zwiększa spodziewany numer następnego pakietu). Jeśli coś się nie zgadza, serwer przesyła komunikat o błędzie. Komunikacja ta odbywa się za pomocą conn.sendall.


### Testowanie

Testowanie polegało na uruchomieniu serwera i klienta, a następnie obserwowaniu logów serwera podczas odbierania i przetwarzania datagramów.

```text2
z21_21_server  | Will listen on  0.0.0.0 : 8888
z21_21_server  | Connected by ('172.21.21.3', 54750)
z21_21_server  |
z21_21_server  | Received packet # 0, length: 512, content:
z21_21_server  |  !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 1, length: 512, content:
z21_21_server  | ?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 2, length: 512, content:
z21_21_server  | ^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 3, length: 512, content:
z21_21_server  | }~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 4, length: 512, content:
z21_21_server  | =>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 5, length: 512, content:
z21_21_server  | \]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 6, length: 512, content:
z21_21_server  | {|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 7, length: 512, content:
z21_21_server  | ;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXY
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 8, length: 512, content:
z21_21_server  | Z[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwx
z21_21_server  |
z21_21_server  |
z21_21_server  | Received packet # 9, length: 512, content:
z21_21_server  | yz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./012345678
z21_21_server  |
z21_21_client  | Sent packet 0 and received confirmation
z21_21_client  | Sent packet 1 and received confirmation
z21_21_client  | Sent packet 2 and received confirmation
z21_21_client  | Sent packet 3 and received confirmation
z21_21_client  | Sent packet 4 and received confirmation
z21_21_client  | Sent packet 5 and received confirmation
z21_21_client  | Sent packet 6 and received confirmation
z21_21_client  | Sent packet 7 and received confirmation
z21_21_client  | Sent packet 8 and received confirmation
z21_21_client  | Sent packet 9 and received confirmation
```

### Uwagi dot. problemów

Największym wyzwaniem było zapewnienie poprawnej komunikacji między klientem a serwerem, szczególnie przy weryfikacji poprawności otrzymanych danych. Problem ten rozwiązano poprzez dodanie szczegółowej weryfikacji danych w serwerze. Istotne okazało się także odwracanie kolejności bajtów w „nagłówku”, za pomocą funkcji htons i htonl – ze względu na konieczność konwersji ze standardu hosta na standard sieciowy (używany do transmisji danych).
Względem wersji UDP należało oczywiście dostosować kod do komunikacji poprzez TCP.

## Zadanie 2.2

### Polecenie

Przerób programy z zadania 2.1 tak, aby posługiwały IPv6.

### Opis rozwiązania

Po stronie klienta (C) zmieniono:

- Strukturę sockaddr_in na sockaddr_in6, a co za tym idzie:
  - Pole `sin6_family` zamiast `sin_family`
  - Pole `sin6_addr` zamiast `sin_addr`
  - Pole `sin6_port` zamiast `sin_port`
- Typ gniazda z `AF_INET` na `AF_INET6`
- Zamiast funkcji resolvera `gethostbyname` użyto `gethostbyname2` z parametrem `AF_INET6`

Po stronie serwera (Python) zmieniono:

- Typ gniazda z `AF_INET` na `AF_INET6`
- Tymczasowy adres hosta z `0.0.0.0` (IPv4) na `::` (IPv6)

### Testowanie

Program został uruchomiony identyczne jak w zadaniu 2.1.

```text
z21_22_server  | Will listen on  :: : 8888
z21_22_server  | Connected by ('fd00:1032:ac21:21::3', 60708, 0, 0)
z21_22_server  | 
z21_22_server  | Received packet # 0, length: 512, content: 
z21_22_server  |  !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>
z21_22_server  | 
z21_22_server  | 
z21_22_server  | Received packet # 1, length: 512, content: 
z21_22_server  | ?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~ !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]
[...]
```

Jak widać po komunikatach z serwera, klient poprawnie nawiązał połączenie po adresie IPv6.

## Zadanie 2.3

### Polecenie

Wychodząc z programu 2.1 zmodyfikuj programy klienta i serwera w następujący sposób:
Klient powinien wysyłać do serwera strumień danych w pętli (tzn. danych powinno być „dużo”,
minimum rzędu kilkuset KB). Serwer powinien odbierać dane, ale między odczytami realizować
sztuczne opóźnienie (np. przy pomocy funkcji sleep()). W ten sposób symulujemy zjawisko
odbiorcy, który „nie nadąża” za szybkim nadawcą. Stos TCP będzie spowalniał nadawcę, aby
uniknąć tracenia danych. Należy zidentyfikować objawy tego zjawiska po stronie klienta (dodając
pomiar i logowanie czasu) i krótko przedstawić swoje wnioski poparte uzyskanymi statystykami
czasowymi. Wskazane jest też przeprowadzenie eksperymentu z różnymi rozmiarami bufora
nadawczego po stronie klienta (np. 100 B, 1 KB, 10 KB)
To zadanie należy wykonać, korzystając z kodu klienta i serwera napisanych w języku C (konieczne
może być napisanie brakującego kodu serwera lub klienta w C w zależności od wariantu zadania


### Opis rozwiązania

W kliencie dodaliśmy pomiar czasu  i pętle w celu uzyskania średnich wartośći z 100 pakietów

pomiar czasu

```

        gettimeofday(&start, NULL);
        if (write(sock, buffer, buffer_size) == -1) bailout("writing on stream socket");
        gettimeofday(&stop, NULL);
```

 pętla w celu uzyskania średnich wartości
```

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
```


server.c 
```
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

```

Serwer tworzy gniazdo powiązane z określonym hostem i portem (metoda bind) i nasłuchuje (listen), oczekując na nawiązanie połączenia (accept – ta metoda zwraca połączenie i adres) . Następnie przy pomocy danych z nagłówków  Odbiera  wiadomość zawartą w datagramie (read) i gdy odbierze cały pakiet idzie spać na chwile.



### Testowanie

Testowanie tak jak w wypadku 2.1 



###Wyniki
dla pakietów o rozmiaże 512 bajtów 
 
z21_23_client  | average time in microseconds: 4, between packages 0 and 1000 
z21_23_client  | average time in microseconds: 811, between packages 1000 and 2000 
z21_23_client  | average time in microseconds: 1135, between packages 2000 and 3000 
z21_23_client  | average time in microseconds: 1289, between packages 3000 and 4000 
z21_23_client  | average time in microseconds: 674, between packages 4000 and 5000 
z21_23_client  | average time in microseconds: 1346, between packages 5000 and 6000 
z21_23_client  | average time in microseconds: 673, between packages 6000 and 7000 
z21_23_client  | average time in microseconds: 1350, between packages 7000 and 8000 
z21_23_client  | average time in microseconds: 1347, between packages 8000 and 9000 
z21_23_client  | average time in microseconds: 677, between packages 9000 and 10000 
z21_23_server  | package number - 8598

dla pakietów 1kb
z21_23_client  | average time in microseconds: 148, between packages 0 and 1000 
z21_23_client  | average time in microseconds: 1000, between packages 1000 and 2000 
z21_23_client  | average time in microseconds: 1365, between packages 2000 and 3000 
z21_23_client  | average time in microseconds: 1019, between packages 3000 and 4000 
z21_23_client  | average time in microseconds: 1016, between packages 4000 and 5000 
z21_23_client  | average time in microseconds: 1020, between packages 5000 and 6000 
z21_23_client  | average time in microseconds: 1022, between packages 6000 and 7000 
z21_23_client  | average time in microseconds: 1360, between packages 7000 and 8000 
z21_23_client  | average time in microseconds: 1018, between packages 8000 and 9000 
z21_23_client  | average time in microseconds: 1018, between packages 9000 and 10000 



###Wnioski
kolejka jest w stanie pomieścić ok 1402*512 bajtów danych
dla pakietów przed tym limitem czas pomiaru jest nie wielki a po zapełnieniu czas ten zbliża się do czasu spania serwera.
