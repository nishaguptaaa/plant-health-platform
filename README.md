# Plant Health Platform

A local-first system for tracking houseplants, their environments, care
histories, health observations, and outcomes over time.

## Goals

- Maintain a longitudinal record for each individual plant
- Support multiple users, households, sites, spaces, and environmental zones
- Track locations, containers, substrates, care events, health issues, and treatments
- Support soil, soilless, semi-hydro, full-water, and mounted cultivation
- Generate explainable care and placement recommendations
- Evaluate whether recommendations actually improve plant health
- Use computer vision and machine learning where appropriate
- Keep private household data and plant photographs out of GitHub
- Remain usable without paid APIs or subscriptions

## Current Status

The project currently includes:

- normalized SQLAlchemy database models
- versioned Alembic database migrations
- users, households, sites, spaces, and environmental zones
- windows, skylights, grow lights, and zone-to-light-source relationships
- species and individual plant records
- propagation, lifecycle, and location history
- containers and container history
- cultivation methods and substrate mixtures
- longitudinal plant-health observations
- watering, fertilizing, repotting, pruning, and other care events
- health issues and treatment outcomes
- tasks, recommendations, and recommendation outcomes
- weather snapshots and an Open-Meteo provider
- manual environmental and light measurements
- a transparent first-pass light estimator
- an initial Streamlit dashboard
- automated tests and Ruff code-quality checks

## Technology

- Python 3.12
- SQLAlchemy
- SQLite for local development
- Alembic database migrations
- Pydantic
- HTTPX
- Streamlit
- pytest
- Ruff
- pandas and scikit-learn in later data-analysis phases
- PyTorch for later computer-vision experiments
- Ollama for optional local language and vision models

## Local Setup

### 1. Open the project

Open the `plant-health-platform` directory in VS Code.

### 2. Create a Python virtual environment

Run:

    python3.12 -m venv venv

Activate it on macOS or Linux:

    source venv/bin/activate

The terminal prompt should begin with `(venv)`.

### 3. Install the project

Run:

    python -m pip install -e ".[dev]"

The editable installation means changes to the source code are immediately
available without reinstalling after every edit.

### 4. Create or update the local database

Run:

    python -m alembic upgrade head

The local SQLite database is created inside `data/private/`. That directory is
ignored by Git.

### 5. Start the Streamlit application

Run:

    python -m streamlit run app/main.py

Open this address if the browser does not open automatically:

    http://localhost:8501

To stop the application, return to the terminal and press `Control + C`.

## Development Checks

Run the code-quality check:

    python -m ruff check .

Run all automated tests:

    python -m pytest

Check that the database models and migrations agree:

    python -m alembic check

Check the current migration:

    python -m alembic current

## Weather Data

The personal prototype uses Open-Meteo through a provider-independent
interface.

The integration:

- requires no API key for qualifying non-commercial use
- sends coordinates rather than requiring a street address
- stores standardized weather snapshots
- tracks cloud cover and solar radiation for future light analysis
- can be replaced with another provider without redesigning the database

Open-Meteo attribution and commercial-use considerations are documented in
`docs/data-sources.md`.

## Light Estimates

The Version 1 light estimator combines:

- outdoor solar radiation
- window transmission
- estimated visible sky
- distance from a light source
- estimated source contribution

It is intended for comparing zones, not claiming exact laboratory-grade lux
values.

Its assumptions and limitations are documented in
`docs/light-estimation.md`.

## Privacy

Private information is excluded from GitHub by default.

Ignored local data includes:

- SQLite databases
- private household data
- uploaded images
- environment-variable files
- generated model artifacts

Plant and room images should be processed temporarily and deleted unless the
user explicitly chooses to retain them.

A full floor plan is not required. The initial system uses named spaces,
environmental zones, light sources, and optional measurements.

## Project Structure

    plant-health-platform/
    ├── app/
    │   └── main.py
    ├── data/
    │   ├── private/
    │   └── reference/
    ├── docs/
    ├── migrations/
    │   └── versions/
    ├── ml/
    ├── models/
    │   └── artifacts/
    ├── notebooks/
    ├── src/
    │   └── plant_health/
    │       ├── database/
    │       ├── light/
    │       └── weather/
    ├── tests/
    ├── pyproject.toml
    └── README.md

## Roadmap

The detailed project plan is available in `docs/product-roadmap.md`.

The next application milestones are:

- household and user setup
- site, room, zone, and light-source forms
- plant catalog forms
- observation and care-entry forms
- plant history pages
- tasks and recommendation views
- weather and environmental dashboards