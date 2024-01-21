# PSI Projekt

## Testy integracyjne automatyczne

### Przygotowanie środowiska

```bash
cd client
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Uruchomienie testów

```bash
cd client
pytest
```

## Testy integracyjne manualne

```bash
docker compose -f docker-compose-double.yml up --build -d
```

Na pierwszym terminalu:

```bash
docker exec -it z21_project_client_1 python -u /client-src/client.py z21_project_server --port 65432
python -u /client-src/client.py z21_project_server --port 65432
```

Na drugim terminalu:

```bash
docker exec -it z21_project_client_2 python -u /client-src/client.py z21_project_server --port 65432
```
