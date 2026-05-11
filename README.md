# Warehouse Management System (WMS)

Full-stack warehouse, order, and AGV automation aligned with the project presentation: **FastAPI** (async API + rules), **SQLAlchemy + SQLite** (persistent store), **JWT auth**, **React 18 + TypeScript + Vite** (operator UI), and a **background AGV simulator** (FastAPI lifespan) that assigns validated orders to idle vehicles and simulates pick → transit → confirmation.

## Prerequisites

- Python 3.11+ (3.12 recommended)
- Node.js 20+ and npm

## Backend (API)

From the `final_product/api` directory:

```bash
pip install -r ../requirements.txt
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

- **OpenAPI / Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

SQLite database file: `final_product/api/warehouse.db` (created on first run).

### Default login (JWT)

| Field    | Value   |
|----------|---------|
| Username | `admin` |
| Password | `admin` |

Override with environment variables: `WMS_ADMIN_USERNAME`, `WMS_ADMIN_PASSWORD`, `WMS_JWT_SECRET`.

### File exports (assignment + backup)

On startup and after relevant mutations, the API can mirror state to:

- `final_product/api/data/orders.csv`
- `final_product/api/data/agvs.csv`
- `final_product/api/data/logs.csv`
- `final_product/api/data/warehouse_audit.log` (append-only text audit lines on each log row)

Authenticated clients may also call `POST /export/snapshot` to regenerate the CSV files. The React **Orders** page includes a **Save server CSV** button that invokes this endpoint.

## Frontend (React)

From `final_product/react_web`:

```bash
npm install
npm run dev
```

- **Dev server:** [http://127.0.0.1:5173](http://127.0.0.1:5173)
- Set `VITE_API_URL` if the API is not at `http://127.0.0.1:8000` (see `.env.example` if present).

### Demo flow (presentation)

1. Log in → Dashboard  
2. Products — create or edit catalog items  
3. Zones — source vs destination; occupancy reflects active orders  
4. Orders — create with priority; status moves **validated → assigned → in_transit**; confirm when **IN TRANSIT**  
5. AGVs — two default units (`AGV-1`, `AGV-2`); simulator uses idle units only  
6. Logs — audit trail  
7. Optional: **Save server CSV** on Orders, or Swagger **Authorize** then `POST /export/snapshot`

## Order lifecycle (API values)

`pending` → `validated` (set in one create transaction) → `assigned` → `in_transit` → `delivered` (after operator confirm), or `cancelled` / `failed`.

## Legacy Tkinter apps

`main.py`, `warehouse_manager.py`, and `order_manager.py` are an older desktop prototype. The graded / presentation stack is **FastAPI + React** above.
