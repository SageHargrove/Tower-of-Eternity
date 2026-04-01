from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

load_dotenv()

from database import init_db
from routers import heroes, gacha, tower, base, runs

app = FastAPI(title="Tower Gacha API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/portraits", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    init_db()
    # Start background portrait cache worker
    from services.portrait_cache import start_cache_worker
    start_cache_worker()
    print("Portrait cache worker started.")

app.include_router(heroes.router, prefix="/heroes", tags=["heroes"])
app.include_router(gacha.router, prefix="/gacha", tags=["gacha"])
app.include_router(tower.router, prefix="/tower", tags=["tower"])
app.include_router(base.router, prefix="/base", tags=["base"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])

@app.get("/")
def root():
    return {"status": "Tower Gacha API running"}

@app.get("/portrait-cache/status")
def cache_status():
    from services.portrait_cache import get_cache_counts
    counts = get_cache_counts()
    total = sum(counts.values())
    return {"counts_by_star": counts, "total_available": total}
