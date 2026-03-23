"""Utilitários de segurança JWT e dependências FastAPI para autenticação/autorização.

Fluxo:
    1. POST /auth/token  →  create_access_token  →  JWT devolvido ao cliente
    2. Cliente envia   `Authorization: Bearer <token>` em cada pedido protegido
    3. get_current_user valida a assinatura e devolve a entidade Usuario
    4. require_write_access adiciona a verificação de role sobre get_current_user;
       lança HTTP 403 se o utilizador for CONVIDADO.

Variáveis de ambiente:
    JWT_SECRET_KEY  – chave de assinatura HMAC-SHA256 (≥ 32 caracteres).
                      Defina sempre em produção; o valor padrão é apenas para dev.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError, jwt

from packages.domain.auth.models import RoleUsuario, Usuario

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

_SECRET_KEY: str = os.getenv(
    "JWT_SECRET_KEY",
    "dev-only-secret-key-nao-usar-em-producao!",  # >= 32 chars, claramente dev
)
_ALGORITHM = "HS256"
_ACCESS_TOKEN_EXPIRE_MINUTES = 60

_bearer = HTTPBearer(auto_error=True)

# ---------------------------------------------------------------------------
# Criação de token
# ---------------------------------------------------------------------------


def create_access_token(
    email: str,
    role: RoleUsuario,
    expires_minutes: int = _ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    """Gera um JWT assinado com sub=email e role=role.value."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": email, "role": role.value, "exp": expire}
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


# ---------------------------------------------------------------------------
# Dependências FastAPI
# ---------------------------------------------------------------------------


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> Usuario:
    """Valida o Bearer token e devolve a entidade Usuario autenticada.

    Lança HTTP 401 se o token estiver ausente, inválido ou expirado.
    """
    _401 = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de autenticacao invalido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            _SECRET_KEY,
            algorithms=[_ALGORITHM],
        )
        email: str = payload.get("sub", "")
        role_str: str = payload.get("role", "")
        if not email or not role_str:
            raise _401
        role = RoleUsuario(role_str)
    except (JWTError, ExpiredSignatureError, ValueError, KeyError):
        raise _401

    return Usuario(email=email, nome=email, role=role)


def require_write_access(
    current_user: Annotated[Usuario, Depends(get_current_user)],
) -> Usuario:
    """Permite apenas ADMIN e ENGENHEIRO; lança HTTP 403 para CONVIDADO."""
    if current_user.role is RoleUsuario.CONVIDADO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso de escrita negado para perfil CONVIDADO.",
        )
    return current_user
