.PHONY: db-up db-down db-logs db-shell db-reset db-status

db-up:
	docker compose up -d --wait postgres

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

db-shell:
	docker compose exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

db-status:
	docker compose ps postgres

# 로컬 DB 데이터를 모두 지우고 스키마를 처음부터 다시 만듭니다.
db-reset:
	docker compose down -v
	docker compose up -d --wait postgres
