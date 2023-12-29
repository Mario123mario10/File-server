# Projekt PSI 2023Z

Skład zespołu nr.21

- Damian Pałyska
- Michał Bogiel
- Mariusz Pakulski
- Jan Kowalczewski

Temat zadania: Serwer plików

Lider zespołu – Mariusz Pakulski (01169219@pw.edu.pl)

## Treść zadania

Serwer plików, udostępniający funkcjonalność pobierania plików przez
klientów, łączących się za pomocą protokołu TCP. Serwer potrafi
obsługiwać wielu klientów jednocześnie, dzięki zastosowaniu
mechanizmu wielowątkowości.

## Interpretacja treści zadania (doprecyzowanie)

Projekt ma na celu stworzenie serwera plików, który umożliwia
użytkownikom pobieranie plików przez połączenia TCP.
Kluczowe aspekty projektu to:

1. Protokół TCP: Serwer wykorzystuje protokół TCP, co gwarantuje
niezawodność przesyłania danych. TCP zapewnia integralność danych,
potwierdzenia odbioru oraz kontrolę przepływu, co jest kluczowe dla
bezpiecznego przesyłania plików.
2. Wielowątkowość: Serwer wykorzystuje mechanizm wielowątkowości,
aby umożliwić równoczesną obsługę żądań od wielu klientów. Dzięki
temu, serwer może efektywnie zarządzać równoległymi połączeniami,
zwiększając swoją skalowalność i wydajność.
3. Pobieranie Plików: Podstawową funkcją serwera jest umożliwienie
klientom pobierania plików. Klienci będą wysyłać żądania określające,
które pliki chcą pobrać, a serwer będzie odpowiedzialny za ich
przesyłanie.

Projekt będzie składał się z 2 programów: serwera oraz klienta. Serwer będzie
udostępniał pliki znajdujące się w jego folderze, zaś klient będzie zapisywał
pobrane pliki w swoim folderze.

## Krótki opis funkcjonalny – „black-box”

- Serwer plików – działa jako centralny węzeł w sieci, realizujący następujące
funkcje:
  - Przechowywanie plików:
    - Przechowuje pliki dostępne do pobrania
    - Zarządza dostępem do nich
  - Obsługa połączeń TCP:
    - Nasłuchuje na określonym porcie na połączenia TCP przychodzące od klientów
    - Ustanawia z nimi połączenia
  - Wielowątkowa obsługa żądań:
    - Dla każdego połączenia klienta, tworzy osobny wątek, umożliwiając równoczesną obsługę wielu żądań
    - Każdy wątek jest odpowiedzialny za obsługę interakcji z pojedynczym klientem
  - Proces przesyłania plików:
    - Po otrzymaniu żądania od klienta, inicjuje i kontroluje przesyłanie pliku do klienta
  - Wyświetlanie listy plików:
    - Po otrzymaniu żądania "ls" od klienta wyświetla zawartość wskazanego w argumencie katalogu. Domyślnie jest to główny katalog serwera
    - Po otrzymaniu żądania "tree" od klienta wyświetla drzewo folderów dla wskazanego w argumencie katalogu. Domyślnie dla głównego katalogu serwera

- Klient – aplikacja kliencka, która komunikuje się z serwerem, realizując następujące funkcje:
  - Inicjowanie połączenia
    - Nawiązuje połączenie TCP z serwerem na określonym porcie.
    - Wysyła żądanie pobrania określonego pliku.
  - Odbiór plików
    - Po otrzymaniu pliku od serwera, zapisuje go w lokalnym systemie plików.
  - Interfejs użytkownika
    - Umożliwia użytkownikowi wprowadzenie nazwy pliku do pobrania
    - Umożliwia użytkownikowi wyświetlenie zawartości lub drzewa folderów dla wskazanego katalogu

## Opis i analiza poprawności stosowanych protokołów komunikacyjnych

Dla naszego projektu kluczowe znaczenie ma zastosowanie protokołu TCP wraz
z IP. TCP zapewnia niezawodność i kontrolę przepływu danych, co jest
niezbędne dla przesyłania plików, podczas gdy IP umożliwia właściwe
adresowanie i routing w sieci. Razem tworzą one solidną podstawę dla
bezpiecznego i efektywnego przesyłania danych w systemie serwera plików.

### Protokół TCP (Transmission Control Protocol)

- Niezawodność: TCP jest protokołem zorientowanym na połączenie, który zapewnia niezawodne przesyłanie danych poprzez potwierdzenia i retransmisję utraconych pakietów.
- Kontrola Przepływu: TCP zarządza kontrolą przepływu danych, co zapobiega przeciążeniu sieci i zapewnia równomierne przesyłanie danych.
- Zastosowanie w Projekcie: W projekcie serwera plików, TCP jest wykorzystywany do nawiązywania stabilnych połączeń z klientami, co jest kluczowe dla przesyłania plików. TCP gwarantuje, że pliki są przesyłane kompletnie i w odpowiedniej kolejności.

### Protokół IP (Internet Protocol)

- Adresacja i Routing: IP odpowiada za adresowanie i dostarczanie pakietów danych do odpowiedniego miejsca docelowego w sieci.
- Bezstanowość i Niezależność: Każdy pakiet danych traktowany jest niezależnie, co pozwala na elastyczność w routingu przez różne ścieżki w sieci.
- Zastosowanie w Projekcie: Protokół IP jest wykorzystywany w połączeniu z TCP do adresowania i dostarczania danych między serwerem a klientami.
Odpowiedź serwera

### Zapytanie klient-serwer

| Nazwa | Typ danych |
|----------|:-------------|
| polecenie | str |
| ścieżka do pliku | str |

### Odpowiedź serwer-klient

## W przypadku pobierania plików:

W przypadku poprawnego zapytania klienta:

| Nazwa | Typ danych |
|----------|:-------------|
| kod błędu | unsigned int 16 = 0 |
| wielkość pliku (B) | unsigned int 64 |
| czas edycji pliku | unsigned int 64 |
| plik | tablica bajtów |

W przypadku niepoprawnego zapytania klienta:

| Nazwa | Typ danych |
|----------|:-------------|
| kod błędu | unsigned int 16 |

możliwe błędy:

- 1 - niepoprawna nazwa pliku
- 2 - niepoprawny katalog
- 3 - inny

## W przypadku wyświetlania listy plików

W przypadku poprawnego zapytania klienta:

| Nazwa | Typ danych |
|----------|:-------------|
| kod błędu | unsigned int 16 = 0 |
| lista plików | str |

W przypadku niepoprawnego zapytania klienta:

| Nazwa | Typ danych |
|----------|:-------------|
| kod błędu | unsigned int 16 |

możliwe błędy:

- 2 - niepoprawny katalog
- 3 - inny

## Planowany podział na moduły i struktura komunikacji

### Moduły

- Moduł Serwera:
  - main(): nasłuchuje na połączenia TCP na określonym porcie i tworzy nowe wątki
  - handle_connection(socket): wywoływana w każdym nowym wątku, odbiera komunikaty od klienta, wywołuje funkcje sprawdzające czy zapytanie jest poprawne, po czym wysyła dane do klienta, i czeka na kolejne zapytanie / zakończenie połączenia.
  - verify_file_path(path) - sprawdza czy dane do klienta są legalne (czy ścieżka do pliku nie wychodzi poza katalog)
  - get_ls(path): pobiera do stringa zawartość wskazanego katalogu
  - get_tree(path): pobiera do stringa drzewo folderów dla wskazanego katalogu

- Moduł Klienta:
  - get_file(path): wysyła komunikat do serwera z prośbą o wysłanie pliku, odbiera go i zapisuje
  - print_ls(path): wysyła komunikat do serwera z prośbą o listę zawartości wskazanego katalogu
  - print_tree(path): wysyła komunikat do serwera z prośbą o drzewo folderów dla wskazanego katalogu
  - main(): łączy się z serwerem i w pętli prosi użytkownika o podanie ścieżki pliku do pobrania

### Struktura Komunikacji

Komunikacja między klientem a serwerem odbywa się przez połączenia
TCP, gdzie serwer obsługuje każde połączenie w osobnym wątku. Klient
inicjuje połączenie, i wysyła żądania dotyczące plików, po czym odbiera i zapisuje pliki przesłane przez serwer lub wyświetla otrzymaną listę plików

## Zarys koncepcji implementacji

- Język Programowania: Python3 (oferuje wsparcie dla sieciowych operacji i wielowątkowości).
- Biblioteki:
  - socket (dla obsługi TCP)
  - threading (dla wielowątkowości)
- Narzędzia: Visual Studio Code (wspiera rozwój i debugowanie)
