# 💳 Credit Approval System

A robust backend system built using **Django** and **PostgreSQL** to manage customer credit data, evaluate loan eligibility, and process loan applications.  
The system supports **automated data ingestion from Excel files**, background processing using **Celery**, and is fully **Dockerized** for easy setup and deployment.

This project was developed as part of a **technical assessment** and focuses on clean architecture, business logic correctness, and production-ready backend practices.

---

## 🚀 Key Features

- **Automated Data Ingestion**
  - Customer and loan data are ingested automatically from Excel files on application startup.
  - Uses Celery background workers to avoid blocking the main application.

- **Credit Scoring Engine**
  - Calculates a credit score (0–100) based on:
    - Past EMI payment behavior
    - Number of loans taken
    - Recent credit activity
    - Debt sustainability vs income

- **Loan Eligibility & Approval**
  - Determines loan approval status in real time.
  - Applies tier-based interest rate adjustments depending on credit score.

- **RESTful API Design**
  - Clean, well-structured API endpoints for:
    - Customer registration
    - Loan eligibility checks
    - Loan creation
    - Loan history retrieval

- **Containerized Deployment**
  - Entire stack runs using Docker Compose.
  - Single command setup for Django, PostgreSQL, Redis, and Celery.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-----|-----------|
Backend Framework | Django 4.2+, Django Rest Framework |
Database | PostgreSQL |
Background Tasks | Celery |
Message Broker | Redis |
Data Processing | Pandas, OpenPyXL |
Containerization | Docker, Docker Compose |

---

## 📂 Project Structure

```
assessment/
├── app/
├── core/
├── migrations/
├── customer_data.xlsx
├── loan_data.xlsx
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Installation & Setup

### Prerequisites
- Docker
- Docker Compose

### Setup

```bash
git clone <your-repository-link>
cd assessment
docker compose up --build
```

---

## 🌐 API Access

Base URL:
```
http://localhost:8000/
```

---

## 🛣️ API Endpoints

| Method | Endpoint | Description |
|------|---------|-------------|
| POST | /api/register | Register a new customer |
| POST | /api/check-eligibility | Check loan eligibility |
| POST | /api/create-loan | Create a loan |
| GET | /api/view-loan/<loan_id> | View loan details |
| GET | /api/view-loans/<customer_id> | View customer loans |

---

## 🧠 Credit Logic

### Credit Score Factors
- EMI payment history
- Number of past loans
- Loans in current year
- Outstanding loan vs income

### Approval Rules

| Score | Result |
|------|-------|
| > 50 | Approved |
| 30–50 | Approved with min 12% interest |
| 10–30 | Approved with min 16% interest |
| < 10 | Rejected |

---

## 💰 EMI Formula

```
A = P (1 + r)^t
EMI = A / months
```

---

## 🧩 Notes

- Data ingestion handled via Celery
- Redis used as broker
- Designed for assessment evaluation

---

## 📄 License

Educational / Assessment use only.
