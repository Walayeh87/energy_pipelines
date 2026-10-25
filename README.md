# Energy Pipelines

A Python backend ETL-project for ingesting, processing, validating, and storing energy time-series data, with a focus on energy-market data and algorithm-driven temperature schedules.

**Status:** Personal portfolio project — work in progress.

## Overview

The project implements two data pipelines:

- **Energy prices:** Fetches day-ahead electricity prices from the [Energy-Charts API](https://api.energy-charts.info/), processes the data, and stores it in PostgreSQL.
- **Temperature schedules:** Retrieves site configurations and electricity prices, generates temperature schedules for cooling systems using an algorithm, validates the results, and stores them in the database.

The pipelines are designed to support multiple sites and algorithms, with database upserts and error handling for data-processing failures.

## Architecture

`External API / PostgreSQL → Data ingestion → Processing & validation → Algorithm execution → PostgreSQL`

Database schema changes are managed with Alembic migrations.
GitHub Actions automates
- database migration checks
- code formatting and linting
- scheduled energy price pipeline execution
- and scheduled schedule temperature pipeline execution

## Tech Stack

- **Python:** pandas, NumPy, SQLAlchemy (and tspropy, a time series processing in Python library created by the auther)
- **Database:** PostgreSQL
- **Migrations:** Alembic
- **Quality & automation:** Ruff, GitHub Actions
- **Data source:** Energy-Charts API

## What This Project Demonstrates

- Building modular Python data pipelines
- Processing and validating time-series data
- Integrating external APIs and relational databases
- Designing database schemas, constraints, and upsert operations
- Implementing algorithm execution and automated workflows

## Setup

Requires Python 3.14 and PostgreSQL. Install dependencies with `pip install -r requirements.txt` and configure `DB_URL` using `.env.example` as a template.

Apply database migrations with `alembic upgrade head` before running the pipelines.
