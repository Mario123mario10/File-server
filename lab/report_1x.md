# PSI 23Z Lab - Sprawozdanie z zadań 1.x

Zespół 21 w składzie:

- Damian Pałyska
- Michał Bogiel
- Mariusz Pakulski
- Jan Kowalczewski

Data: 29.11.2023  
Wersja 1.

## Polecenie (wariant Aa)

Zadanie 1 Komunikacja UDP

Napisz zestaw dwóch programów – klienta i serwera wysyłające datagramy UDP. Wykonaj
ćwiczenie w kolejnych inkrementalnych wariantach (rozszerzając kod z poprzedniej wersji).

### 1.1

Klient wysyła, a serwer odbiera datagramy o stałym rozmiarze (rzędu kilkuset bajtów).  
Datagramy powinny posiadać ustaloną format danych: pierwsze cztery bajty zawierają numer kolejny pakietu (liczony od 0, typ int32), kolejne dwa bajty datagramu powinny zawierać informację o jego długości (typ int16), a kolejne bajty to kolejne [drukowalne znaki](https://en.wikipedia.org/wiki/ASCII#Printable_characters) powtarzające się wymaganą liczbę razy, aby osiągnąć zakładany rozmiar.  
Odbiorca powinien weryfikować odebrany datagram i odsyłać odpowiedź (potwierdzenie) o ustalonym formacie. Serwer powinien sygnalizować brak pakietu (przeskok w numeracji pakietu).  
Może być pomocne użycie pakietu struct w Python do konstrukcji i odbierania danych w zadanym
formacie.

Klient w C, serwer w Python.

Można także napisać wersje klienta i serwera w obu językach, ale muszą ze sobą współpracować. Należy zwrócić uwagę na rozmiary danych odczytanych z funkcji sieciowych i weryfikować z rozmiarem przesłanym w „nagłówku” danych. Sygnalizować rozbieżność.

### 1.2

Na bazie kodu z zadania 1.1 napisać klienta, który wysyła kolejne datagramy o przyrastającej wielkości o np. 256 bajtów. Sprawdzić, jaki był maksymalny rozmiar wysłanego (przyjętego) datagramu. Zaproponować algorytm (niekoniecznie implementować) takiego sterowania rozmiarem pakietów, aby jak najszybciej ustalić ten rozmiar z dokładnością do jednego bajta. Po tym zakończyć program klienta. Wyjaśnić.

To zadanie można wykonać, korzystając z kodu klienta i serwera napisanych w C lub w Pythonie (tak jak wskazano w zadaniu 1.1). Nie trzeba tworzyć wersji w obydwu językach.

### 1.3

Uruchomić program z przykładu 1.1 w środowisku symulującym błędy gubienia pakietów. (Informacja o tym jak to zrobić znajduje się w skrypcie opisującym środowisko Dockera). Rozszerzyć protokół i program tak, aby gubione pakiety były wykrywane i retransmitowane.

## Platforma testowa

Do testów wykorzystujemy kontenery Docker uruchamiane przez plik docker-compose.  
W każdym zadaniu występują dwa kontenery:

- Kontener z_21_1x_client dla klienta bazujący na gcc w wersji 4.9
- Kontener z_21_1x_server dla serwera bazujący na obrazie python w wersji 3

Kontenery komunikują się między sobą w sieci z21_network, czyli 172.21.21.0/24.

## Opis rozwiązania

### Zadanie 1.1

### Zadanie 1.2

<!-- wersja robocza -->
proponowany algorytm
1.1   zwieksz rozmiar wiadomości 2 krotnie
1.2 spróbuj wysłać
1.3 jeśli się udało powróć do 1.1
2.0 potega2= rozmiar
2.1 potega2=potega2/2
2.2 maxrozzmiar+=potega2
2.3 jeśli udało się przesłać  powrót do 2.1
2.4 jeśłi nie maxrozmiar-=potega2
2.5poowrót do 2.1

### Zadanie 1.3
