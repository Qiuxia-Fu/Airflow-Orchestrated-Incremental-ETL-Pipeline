# Airflow-Orchestrated Daily ETL Pipeline

[![CI](https://github.com/Qiuxia-Fu/Olist-Airflow-Daily-ETL/actions/workflows/ci.yml/badge.svg)](https://github.com/Qiuxia-Fu/Olist-Airflow-Daily-ETL/actions/workflows/ci.yml)

A production-style, incremental ETL pipeline that extracts daily e-commerce order data, validates and loads it idempotently into PostgreSQL, and transforms it with dbt — fully orchestrated by Apache Airflow, containerized with Docker, and validated on every pull request by a GitHub Actions CI pipeline.

This project extends the [Olist E-Commerce Data Warehouse](https://github.com/Qiuxia-Fu/Olist-E-Commerce-Order-Data-Warehouse) (a dbt-based dimensional warehouse) by adding orchestration, incremental processing, and automated testing on top of it — moving from a one-off batch load to an end-to-end, production-style workflow.

---
## Architecture
raw_source/*.csv (daily files)
|
v
+----------------+ +---------------+ +---------------+ +-----------+
| extract_task |---->| validate_task |---->| load_task |---->| dbt_run |
| watermark-based| | schema/null/ | | idempotent | | stg model |
| incremental read| | dup checks | | Postgres write| | + tests |
+----------------+ +---------------+ +---------------+ +-----------+
(Apache Airflow DAG - daily schedule, automatic retries)
All four tasks run inside Docker containers (Airflow + PostgreSQL), managed by Docker Compose.

---
## Key design decisions

**Incremental extraction with a watermark.** Instead of reprocessing the full dataset every run, the pipeline tracks the last successfully extracted date in a watermark file and only pulls data newer than that — the same pattern used by most production CDC/batch pipelines.

**Idempotent writes.** Data is loaded into PostgreSQL with `INSERT ... ON CONFLICT (order_id) DO NOTHING`, so a task retry or pipeline re-run after a crash never produces duplicate rows. Combined with strict task ordering (load happens, then the watermark advances — never the reverse), the pipeline is safe to fail and re-run at any point without manual cleanup.

**Hybrid ETL/ELT.** Lightweight validation (schema, nulls, duplicates) happens before load, in Python — cheap and fast to fail early on bad data. Heavier transformation logic lives in dbt, running in-warehouse after load. This was validated in practice: when a `dbt run` step failed independently of the load step, the extract-and-load work was preserved and only the transformation needed retrying, confirming that E/L and T are decoupled and independently retriable.

**Containerized for reproducibility.** Airflow and PostgreSQL both run in Docker via Docker Compose, with dbt's `profiles.yml` reading credentials from environment variables (`env_var()`) rather than a machine-level config file — so the whole stack spins up identically on any machine, or in CI, with a single `docker-compose up`.

---
## CI/CD

Every pull request automatically runs two parallel GitHub Actions jobs:

- **`test`** — pytest unit tests covering the extraction and validation logic (duplicate/null detection, watermark-based date filtering)
- **`dbt`** — spins up a throwaway PostgreSQL service container, seeds it with sample data, and runs `dbt build`, which both materializes the staging model and runs dbt data tests (`unique`, `not_null`) against it

This catches both logic bugs (Python) and data-quality regressions (SQL/dbt) before anything merges to `main`.

---
## Tech stack

Apache Airflow · PostgreSQL · dbt · Docker & Docker Compose · pandas · SQLAlchemy · pytest · GitHub Actions

---
## Project structure
airflow-daily-etl/
├── dags/ # Airflow DAG definition
├── extract/ # Extraction, validation, and load logic (also runs standalone via CLI)
├── dbt/ # dbt project (staging model + tests, extended from the Olist warehouse project)
├── docker/ # Postgres init SQL, CI sample data
├── tests/ # pytest unit tests
├── .github/workflows/ # CI pipeline
├── Dockerfile
└── docker-compose.yml

---
## Running locally

```bash
git clone https://github.com/Qiuxia-Fu/Olist-Airflow-Daily-ETL.git
cd Olist-Airflow-Daily-ETL/airflow-daily-etl
cp .env.example .env        # fill in local credentials
docker-compose up -d --build
```

Airflow UI available at `localhost:8080`.
