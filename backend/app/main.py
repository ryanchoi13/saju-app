from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import router

app = FastAPI(title="운세의신 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "name": "fortune-god"}
