from fastapi import Header, HTTPException, status

from app.core.config import get_settings

settings = get_settings()


def require_admin_key(x_admin_key: str = Header(...)) -> None:
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave administrativa inválida.",
        )
