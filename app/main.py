from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Donizo Smart Semantic Pricing Engine v0")
app.include_router(router)

@app.get("/")
def index():
    return {"message": "Donizo Pricing Engine v0", "docs": "/docs"}
