#!/usr/bin/env bash
set -euo pipefail

# 1️⃣ clone base repo & checkout branch
git clone https://github.com/nullroute-commits/Cursor.git && cd Cursor
git checkout feature/full-operational-status

# 2️⃣ create minimal project layout
mkdir -p backend frontend db scripts tests
touch backend/__init__.py frontend/__init__.py

# 3️⃣ write shared requirements (Python 3.12 compatible)
cat > requirements.txt <<'REQ'
fastapi[all]==0.110.*
uvicorn[standard]==0.27.*
sqlmodel==0.0.16
psycopg[binary]==3.2.*
python-dotenv==1.0.*
REQ

# 4️⃣ backend FastAPI app (app.py)
cat > backend/app.py <<'PY'
import os
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel
from enum import Enum
from uuid import UUID, uuid4

class PanelType(str, Enum):
    COMIC="comic"; WIZARD="wizard"; INTERACTIVE="interactive"

class Panel(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    type: PanelType
    title: str
    body: str = ""
    media_url: str | None = None
    meta: dict | None = None

engine = create_engine(os.getenv("DATABASE_URL"))
SQLModel.metadata.create_all(engine)

app = FastAPI(title="Cursor")

class PanelIn(BaseModel):
    type: PanelType; title:str; body:str|None=None; media_url:str|None=None; meta:dict|None=None

@app.post("/api/panels", response_model=Panel)
def create(p:PanelIn):
    with Session(engine) as s:
        panel=Panel(**p.dict())
        s.add(panel); s.commit(); s.refresh(panel)
        return panel

@app.get("/api/panels/{pid}", response_model=Panel)
def read(pid:UUID):
    with Session(engine) as s:
        stmt=select(Panel).where(Panel.id==pid)
        panel=s.exec(stmt).first()
        if not panel: raise HTTPException(404,"not found")
        return panel

@app.put("/api/panels/{pid}", response_model=Panel)
def update(pid:UUID, p:PanelIn):
    with Session(engine) as s:
        panel=s.get(Panel,pid)
        if not panel: raise HTTPException(404,"not found")
        for k,v in p.dict().items(): setattr(panel,k,v)
        s.add(panel); s.commit(); s.refresh(panel)
        return panel

@app.delete("/api/panels/{pid}")
def delete(pid:UUID):
    with Session(engine) as s:
        panel=s.get(Panel,pid)
        if not panel: raise HTTPException(404,"not found")
        s.delete(panel); s.commit()
        return {"ok":True}
PY

# 5️⃣ frontend serves static + Jinja2 templates (main.py)
cat > frontend/main.py <<'PY'
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app=FastAPI()
app.mount("/static",StaticFiles(directory="static"), name="static")
templates=Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(req:Request):
    return templates.TemplateResponse("index.html", {"request":req})
PY

# 6️⃣ minimal template (templates/index.html)
mkdir -p frontend/templates frontend/static
cat > frontend/templates/index.html <<'HTML'
<!doctype html><html><head><title>Cursor</title></head>
<body><h1>Cursor Demo</h1>
<p>Use <code>/api/panels</code> endpoints.</p>
</body></html>
HTML

# 7️⃣ dockerfiles (shared multi‑stage, ARG switches)
cat > backend/Dockerfile <<'DF'
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/. .
FROM python:3.12-slim
WORKDIR /app
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /src .
EXPOSE 8000
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8000"]
DF

cat > frontend/Dockerfile <<'DF'
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY frontend/. .
FROM python:3.12-slim
WORKDIR /app
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /src .
EXPOSE 8080
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8080"]
DF

# 8️⃣ docker‑compose (dev)
cat > docker-compose.yml <<'YML'
version: "3.9"
services:
  db:
    image: postgres:17.6
    environment:
      POSTGRES_USER: cursor
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: cursor
    volumes:
      - pgdata:/var/lib/postgresql/data
  backend:
    build: ./backend
    env_file: .env
    depends_on: [db]
    ports: ["8000:8000"]
  frontend:
    build: ./frontend
    env_file: .env
    depends_on: [backend]
    ports: ["8080:8080"]
volumes:
  pgdata:
YML

# 9️⃣ .env (example – replace PASSWORD before running)
cat > .env <<'ENV'
DATABASE_URL=postgresql+psycopg://cursor:${POSTGRES_PASSWORD}@db:5432/cursor
POSTGRES_PASSWORD=changeme
ENV

# 10️⃣ quick test run
docker compose up -d --build
echo "⏳ waiting for DB…"
sleep 5
docker exec $(docker ps -qf "name=cursor_db") pg_isready -U cursor
echo "✅ services up: http://localhost:8080  &  http://localhost:8000/docs"