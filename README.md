# AgriMarket Intelligence

> **Smart Decisions. Better Markets. Higher Returns.**

A full-stack agricultural technology platform that helps farmers make data-driven selling decisions by combining market intelligence, machine learning price prediction, transport cost estimation, and direct buyer-farmer matching.

---

## Problem Statement

Farmers face a complex set of decisions at every harvest:

- **Where to sell** — which market offers the best price today?
- **When to sell** — is now the right time, or should they wait?
- **What price to expect** — what will the market pay next week?
- **How transportation affects returns** — does a higher-priced distant market actually yield more net profit?
- **How to connect with buyers** — who is buying, at what volume, and at what terms?

Without real-time data and analytical tools, these decisions rely on word-of-mouth and guesswork — often leaving money on the table.

**Core question:**

> *"Where should I sell my produce to get the best expected return?"*

AgriMarket Intelligence answers this with a unified platform that integrates market data, predictive modelling, transport estimation, and direct seller-buyer matching.

---

## Key Features

### For Farmers
- Compare live prices across multiple APMC markets
- View historical price trends and seasonal patterns
- Get ML-powered price forecasts (next 1, 3, or 7 days)
- Receive intelligent market recommendations based on net return after transport
- Discover verified buyers posting requirements for your crops
- Send and receive interest requests directly
- Track all activity from a unified dashboard

### For Buyers
- Post crop procurement requirements with target price and quantity
- Automatically see matched farmers based on crop type and location
- Send interest requests and receive responses
- View farmer contact details after acceptance
- Track all procurement activity from a dashboard

### For Platform Administrators
- Monitor platform-wide statistics (users, markets, recommendations, interests)
- Manage user accounts (activate/deactivate)
- Inspect farmer and buyer records
- View market and pricing data
- Review platform activity

---

## Technology Stack

### Frontend
| Technology | Purpose |
|---|---|
| React 18 | UI library |
| Vite | Build tooling and dev server |
| Tailwind CSS | Utility-first styling |
| React Router v6 | Client-side routing |
| Axios | HTTP client with JWT interceptor |
| Recharts | Data visualisation |
| Lucide React | Icon library |

### Backend
| Technology | Purpose |
|---|---|
| Python 3.11 | Language |
| FastAPI | Web framework |
| Uvicorn | ASGI server |
| SQLAlchemy 2.x | ORM |
| Alembic | Database migrations |
| Pydantic v2 | Data validation and settings |
| python-jose | JWT authentication |
| passlib / bcrypt | Password hashing |

### Database
| Technology | Purpose |
|---|---|
| PostgreSQL 15 | Production database |
| SQLite | Test and development (in-memory) |

### Machine Learning
| Technology | Purpose |
|---|---|
| Pandas | Data processing |
| NumPy | Numerical operations |
| Scikit-learn | Model training (Linear Regression, Ridge) |
| Joblib | Model serialisation |

### Infrastructure
| Technology | Purpose |
|---|---|
| Docker | Containerisation |
| Docker Compose | Multi-service orchestration |
| Alembic | Schema migration management |
| Git | Version control |

---

## Architecture Overview

```
┌─────────────────────┐     HTTP/JSON     ┌─────────────────────────┐
│  React Frontend     │ ◄───────────────► │  FastAPI Backend         │
│  (Vite / Nginx)     │                   │  (Uvicorn / Python)      │
│  Port 3000 / 5173   │                   │  Port 8000               │
└─────────────────────┘                   └──────────┬──────────────┘
                                                      │
                                          ┌───────────▼──────────────┐
                                          │  PostgreSQL Database      │
                                          │  Port 5432               │
                                          └──────────────────────────┘
                                                      │
                                          ┌───────────▼──────────────┐
                                          │  ML Model Artefacts       │
                                          │  ml/models/*.joblib       │
                                          └──────────────────────────┘
```

**Authentication:** JWT Bearer tokens. The frontend stores the token in `localStorage` and attaches it via an Axios interceptor. Role-based access control is enforced on every backend endpoint.

**Roles:** `FARMER`, `BUYER`, `ADMIN`. Public registration is available for `FARMER` and `BUYER`. Admin accounts are created via the `scripts/create_admin.py` helper.

---

## Project Structure

```
AgriMarket_Intelligence/
├── backend/
│   ├── app/
│   │   ├── api/            # Route handlers (auth, farmer, market, ...)
│   │   ├── core/           # Config, security, settings
│   │   ├── database/       # Session, seed data
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic layer
│   │   └── utils/          # Shared utilities
│   ├── alembic/            # Database migrations
│   ├── tests/              # Pytest test suite
│   ├── scripts/            # Admin creation helper
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # Shared UI components
│   │   ├── pages/          # Route-level page components
│   │   ├── layouts/        # AppLayout (sidebar + nav)
│   │   ├── services/       # API service modules
│   │   ├── context/        # Auth context
│   │   ├── hooks/          # Custom hooks
│   │   └── constants/      # Routes, enums
│   ├── .env.example
│   ├── nginx.conf
│   └── Dockerfile
├── ml/
│   ├── data/               # Development price dataset (synthetic)
│   ├── models/             # Trained model artefacts + registry
│   ├── preprocessing/      # Feature engineering
│   ├── training/           # Training pipeline
│   └── reports/            # Model comparison reports
├── data/
│   ├── raw/                # Source datasets
│   └── processed/          # Cleaned/transformed datasets
├── docs/                   # Project documentation
├── docker-compose.yml
└── README.md
```

---

## Local Development Setup

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 15+ (for full functionality; tests use SQLite)

---

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/AgriMarket_Intelligence.git
cd AgriMarket_Intelligence
```

---

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, FRONTEND_URL
```

---

### 3. Database Setup (PostgreSQL)

```bash
# Create the database
createdb agrimarket

# Edit backend/.env:
# DATABASE_URL=postgresql://user:password@localhost:5432/agrimarket
# SECRET_KEY=your-secret-key-here

# Run migrations
alembic upgrade head

# Verify current migration
alembic current

# Seed development data (crops, markets, sample prices)
python -m app.database.seed
```

---

### 4. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

- API: [http://localhost:8000](http://localhost:8000)
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- DB Health: [http://localhost:8000/api/health/db](http://localhost:8000/api/health/db)

---

### 5. Frontend Setup

```bash
cd frontend

# Configure environment
cp .env.example .env
# Set VITE_API_BASE_URL=http://localhost:8000 (default)

# Install dependencies
npm install

# Start development server
npm run dev
```

- Frontend: [http://localhost:5173](http://localhost:5173)

---

### 6. Create an Admin Account

```bash
cd backend
python scripts/create_admin.py
```

Follow the prompts to create the first admin account.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/agrimarket` |
| `SECRET_KEY` | JWT signing secret (keep secret, min 32 chars) | `your-secret-key-here` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token validity | `60` |
| `FRONTEND_URL` | Allowed CORS origin | `http://localhost:5173` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `ADMIN_EMAIL` | Seed admin email (dev only) | `admin@example.com` |
| `ADMIN_PASSWORD` | Seed admin password (dev only) | `changeme123` |

### Frontend (`frontend/.env`)

| Variable | Description | Example |
|---|---|---|
| `VITE_API_BASE_URL` | Backend base URL | `http://localhost:8000` |

> **Security:** Never commit `.env` files with real credentials. The repository `.gitignore` excludes `.env` by default.

---

## Database Migrations (Alembic)

```bash
# Apply all pending migrations
alembic upgrade head

# Show current migration
alembic current

# Show migration history
alembic history

# Roll back one migration
alembic downgrade -1

# Create a new migration
alembic revision --autogenerate -m "description"
```

### Migration History

| Revision | Description |
|---|---|
| `0001_initial_schema` | All core tables: users, farmers, buyers, crops, markets, market_prices, buyer_requirements, recommendations, transaction_interests |
| `0002_farmer_crops` | Farmer crop listings (FarmerCrop) |
| `0003_recommendation_fields` | Extended recommendation output fields |
| `0004_phase9_buyer_farmer_market` | Buyer-farmer interest and matching fields |

---

## Running Tests

```bash
cd backend

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py -v

# Run excluding known environment-limited test
pytest --ignore=tests/test_prediction.py
```

### Test Coverage by Phase

| Test File | Coverage |
|---|---|
| `test_health.py` | Health endpoints |
| `test_database.py` | Database schema, models, constraints |
| `test_auth.py` | Registration, login, JWT, role validation |
| `test_farmer.py` | Farmer profile, crop management |
| `test_market.py` | Market prices, history, comparison |
| `test_transport.py` | Transport distance and cost estimation |
| `test_prediction.py` | ML prediction API *(see Known Limitations)* |
| `test_recommendation.py` | Recommendation engine |
| `test_buyer.py` | Buyer profile, requirements, matching, interests |
| `test_dashboard.py` | Farmer/buyer dashboard aggregation APIs |
| `test_admin.py` | Admin endpoints, user management, role isolation |
| `test_phase12.py` | Security, IDOR, input validation, CORS, headers |

---

## Docker Deployment

### Quick Start

```bash
# 1. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env — set SECRET_KEY and other values

# 2. Build and start all services
POSTGRES_PASSWORD=your-secure-password docker compose up --build

# Services:
#   PostgreSQL  → localhost:5432
#   Backend API → http://localhost:8000
#   Frontend    → http://localhost:3000
```

### Production Notes

- Set `SECRET_KEY` to a cryptographically random string (32+ chars)
- Set `FRONTEND_URL` to your actual domain
- Set `VITE_API_BASE_URL` to your public API URL before building the frontend
- Use a proper PostgreSQL password — never the default
- Place the stack behind a reverse proxy (nginx, Caddy, Traefik) with TLS for production

---

## API Documentation

FastAPI generates interactive documentation automatically.

With the backend running:

| Interface | URL |
|---|---|
| Swagger UI (interactive) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| ReDoc (readable) | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| OpenAPI JSON | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) |

### API Prefixes

| Prefix | Module |
|---|---|
| `/api/health` | Health check |
| `/api/auth` | Authentication (register, login, me) |
| `/api/farmer` | Farmer profile and crops |
| `/api/market` | Market prices and comparison |
| `/api/crops` | Crop catalogue |
| `/api/transport` | Transport cost estimation |
| `/api/prediction` | ML price prediction |
| `/api/recommendation` | Smart market recommendation |
| `/api/buyer` | Buyer profile and requirements |
| `/api/interests` | Buyer-farmer interest requests |
| `/api/dashboard` | Role-specific dashboard aggregation |
| `/api/admin` | Admin platform management |

---

## Known Limitations

1. **Development market data is synthetic.** The current price dataset (`ml/data/dev_prices.csv`) was generated procedurally for development and testing purposes. It does not represent real-time government market prices or historical APMC data.

2. **ML prediction accuracy is limited.** Models are trained on synthetic data only. Prediction outputs should not be used for real financial decisions. The model achieves reasonable RMSE on development data but has no guarantees on real market behaviour.

3. **Transport cost is estimated.** Transport estimates use a configurable formula (`base_cost + distance_km × rate_per_km × quantity`). They are not commercial transport quotes and do not account for road conditions, seasonal variation, or commodity-specific handling.

4. **`test_prediction.py` may be blocked by Windows Application Control.** On some Windows configurations, importing `pandas` in a subprocess context during pytest can fail with a DLL policy violation. This is an environment-level restriction, not a code defect. The test is not modified or skipped — it is run on every test cycle and reported accurately. On Linux/macOS and unmanaged Windows systems, all prediction tests pass.

5. **No real-time data feed.** The platform does not currently connect to any live agricultural price API. Prices must be entered or seeded manually.

6. **No notification system.** Interest request notifications are visible only within the platform dashboard — no email or SMS notifications are implemented.

7. **PostgreSQL required for production.** The test suite runs on SQLite in-memory. Production deployment requires PostgreSQL 15+.

---

## Future Improvements

- Integration with government agricultural price APIs (e.g., Agmarknet, eNAM)
- Real-time notifications (email, SMS, push)
- Improved ML models with real historical data
- Multi-language support (Tamil, Hindi, regional languages)
- Mobile app (React Native)
- Advanced analytics and seasonal trend reports
- Logistics partner integration
- Cooperative/FPO multi-farmer management
- Quality grading and certification tracking

---

## Completed Development Phases

| Phase | Description | Commit |
|---|---|---|
| 1 | Project Setup & Architecture | `083c22b` |
| 2 | PostgreSQL Database & Models | `fa83dd0` |
| 3 | Authentication & Authorization | `75f9efe` |
| 4 | Farmer Module | `924c189` |
| 5 | Market Intelligence | `50887a4` |
| 6 | Location & Transport Cost | `93325be` |
| 7 | ML Price Prediction | `0c2abea` |
| 8 | Recommendation Engine | `51f5408` |
| 9 | Direct Buyer-Farmer Market Access | `ff83c54` |
| 10 | Dashboard & Analytics | `aa1ebdc` |
| 11 | Admin Panel | `d35cf7d` |
| 12 | Integration, Security & Error Handling | `d37f188` |
| 13 | UI/UX Polish & Responsive Design | `dc5afb6` |
| 14 | Final Testing, Documentation & Deployment | *(this phase)* |

---

## License

MIT License — see [LICENSE](./LICENSE) for details.
