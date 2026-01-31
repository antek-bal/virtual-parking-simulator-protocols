# Virtual Parking Simulator

**Author:** Antoni Balcerzak
**Group:** 1

## Project Description
The **Virtual Parking Simulator** is a backend application built with **FastAPI** designed to manage a multi-level parking system. It handles vehicle entries, real-time parking fee calculations based on a progressive pricing strategy, and secure exit processing.

### Key Features:
* **Validation:** Advanced registration number validation for Polish plates, including length and region-specific prefix checks.
* **Pricing Engine:** Automated fee calculation with a 30-minute grace period (free parking) and floor-dependent hourly rates.
* **Session Management:** Enforces a 15-minute exit window after payment is completed.
* **History Tracking:** All completed parking sessions are archived for administrative review.



## Installation and Setup

### Requirements
* Python 3.12+
* Pip (Python package manager)

### Installation
1.  Clone the repository to your local machine.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application
To start the FastAPI server locally, run:
```bash
uvicorn src.app.main:app --reload
```
The API documentation (Swagger UI) will be available at: `http://127.0.0.1:8000/docs`.

## Testing and Pipelines
This project implements a testing strategy integrated with **GitHub Actions** for Continuous Integration.

### 1. Unit Tests
Focuses on core business logic (Pricing, Validation, Parking Management).
* **Execution:** `pytest tests/unit`
* **Pipeline:** Handled by `python-app.yml`.

### 2. API & BDD Tests
Tests HTTP endpoints and business scenarios using **Behave** (Gherkin).
* **Execution:** `pytest tests/api` and `behave`
* **Pipeline:** Handled by `api-tests.yml`.

### 3. Performance Tests
Verifies system stability and latency by simulating 1000+ concurrent operations.
* **Execution:** `pytest tests/perf`
* **Threshold:** Each operation must complete in less than 0.5s.
* **Pipeline:** Handled by `performance-tests.yml`.

## Project Structure
```plaintext
virtual-parking-simulator/
├── src/
│   └── app/                    # Main application logic
│       ├── services/           # Business logic implementations
│       └── main.py             # FastAPI entry point
├── tests/                      # Test suites (Unit, API, Perf)
├── features/                   # BDD Gherkin scenarios
├── requirements.txt            # Project dependencies
└── .github/workflows/          # CI/CD pipeline configurations
