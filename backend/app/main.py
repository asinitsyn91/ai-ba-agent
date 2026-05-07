from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(
    title="AI-ba-agent",
    description="Бизнес-аналитик-Корпоративный архитектор: извлечение требований по Volere/EARS/BABOK",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"service": "AI-ba-agent", "version": "1.0.0", "docs": "/docs"}
