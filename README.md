# AgriMarket Intelligence

> **Smart Decisions. Better Markets. Higher Returns.**

A full-stack agricultural technology platform that helps farmers make data-driven selling decisions by combining market intelligence, machine learning price prediction, and smart recommendations.

---

## Problem Statement

Farmers face a complex set of decisions at every harvest:

- **Where to sell** — which market offers the best price today?
- **When to sell** — is now the right time, or should they wait?
- **What price to expect** — what will the market pay next week?
- **How transportation affects returns** — does a higher-priced distant market actually yield more net profit?
- **How to connect with buyers** — who is buying, at what volume, and at what terms?

Without real-time data and analytical tools, these decisions rely on word-of-mouth and guesswork — often leaving money on the table.

AgriMarket Intelligence addresses this by providing a unified platform that integrates market data, predictive modelling, and seller-buyer matching.

---

## Planned Modules

| # | Module | Description |
|---|--------|-------------|
| 1 | **Farmer Management** | Farmer profiles, farms, crops, and selling history |
| 2 | **Market Intelligence** | Real-time price comparison across markets |
| 3 | **Location & Transportation Analysis** | Transport cost calculation and route optimisation |
| 4 | **Price Prediction** | ML-based crop price forecasting |
| 5 | **Smart Selling Recommendation** | Optimal market and timing recommendations |
| 6 | **Buyer Marketplace** | Direct farmer-buyer discovery and matching |
| 7 | **Analytics Dashboard** | Visual insights and historical trends |
| 8 | **Admin Management** | Platform administration and data management |

---

## Technology Stack

### Frontend
- **React** — UI library
- **Vite** — build tooling and dev server
- **Tailwind CSS** — utility-first styling
- **React Router** — client-side routing
- **Axios** — HTTP client
- **Lucide React** — icon library

### Backend
- **FastAPI** — high-performance Python web framework
- **Uvicorn** — ASGI server
- **Pydantic** — data validation and settings management
- **SQLAlchemy** — ORM (Phase 2+)

### Database
- **PostgreSQL** — relational database (Phase 2+)

### Machine Learning
- **Scikit-learn** — ML model training and inference (Phase 4+)

---

## Development Status

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Project Setup & Architecture | ✅ Completed |
| Phase 2 | Database & Farmer Management | Planned |
| Phase 3 | Authentication & Authorisation | Planned |
| Phase 4 | Market Intelligence | Planned |
| Phase 5 | Price Prediction ML | Planned |
| Phase 6 | Smart Recommendations | Planned |
| Phase 7 | Buyer Marketplace | Planned |
| Phase 8 | Analytics Dashboard | Planned |

---

## Project Structure

```
AgriMarket_Intelligence/
├── frontend/          # React + Vite application
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── layouts/
│       ├── services/
│       ├── hooks/
│       ├── utils/
│       └── constants/
├── backend/           # FastAPI application
│   └── app/
│       ├── api/
│       ├── core/
│       ├── models/
│       ├── schemas/
│       ├── services/
│       ├── database/
│       └── utils/
├── data/              # Raw and processed datasets
├── ml/                # ML models, notebooks, training scripts
└── docs/              # Project documentation
```

---

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 15+ (Phase 2+)

---

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values

# Start the development server
uvicorn app.main:app --reload
```

API will be available at `http://localhost:8000`

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/api/health`

---

### Frontend

```bash
cd frontend

# Configure environment
cp .env.example .env

# Install dependencies
npm install

# Start the development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

### Running Tests

```bash
cd backend
pytest
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | Application secret key |
| `CORS_ORIGINS` | Allowed frontend origins (comma-separated) |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Backend API base URL |

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
