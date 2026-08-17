.PHONY: test run install build up down logs backup

test:
	venv\Scripts\pytest tests\ -v --tb=short

run:
	venv\Scripts\python main.py

install:
	venv\Scripts\pip install -r requirements.txt

build:
	docker build -t tozalash_servis .

up:
	docker-compose -f docker-compose.prod.yml up -d

down:
	docker-compose -f docker-compose.prod.yml down

logs:
	docker-compose -f docker-compose.prod.yml logs -f

backup:
	venv\Scripts\python scripts\backup_db.py
