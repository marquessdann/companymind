import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import OpenAIError

from app.api.v1 import chat, search, documents, admin, system
from app.core.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("companymind")

app = FastAPI(
    title="CompanyMind AI",
    description="Corporate Knowledge & AI Integration Platform — RAG sobre dados corporativos.",
    version="0.1.0",
)

# CORS restrito às origens conhecidas (ver Settings.allowed_origins),
# em vez de aberto para qualquer site — os endpoints de /chat e /search
# chamam a API da OpenAI a cada request, então CORS aberto == qualquer
# site podendo gastar seu crédito de API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)


@app.exception_handler(OpenAIError)
async def openai_error_handler(request: Request, exc: OpenAIError) -> JSONResponse:
    """Erros da API da OpenAI (timeout, rate limit, indisponibilidade)
    não devem virar um 500 cru com stack trace para o usuário."""
    logger.exception("Erro ao chamar a API da OpenAI")
    return JSONResponse(
        status_code=502,
        content={
            "detail": "O serviço de IA está indisponível no momento. Tente novamente em instantes."
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Rede de segurança final: loga o erro real nos logs do servidor,
    mas nunca devolve detalhes internos (stack trace, nomes de tabela,
    etc.) na resposta HTTP."""
    logger.exception("Erro não tratado")
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu um erro interno inesperado."},
    )


app.include_router(chat.router)
app.include_router(search.router)
app.include_router(documents.router)
app.include_router(admin.router)
app.include_router(system.router)
