from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import chat, search, documents, admin, system

app = FastAPI(
    title="CompanyMind AI",
    description="Corporate Knowledge & AI Integration Platform — RAG sobre dados corporativos.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(search.router)
app.include_router(documents.router)
app.include_router(admin.router)
app.include_router(system.router)
