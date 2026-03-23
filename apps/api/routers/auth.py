"""Rota de autenticação provisória — devolve JWT para qualquer email.

Nota: esta rota é um mock temporário para viabilizar testes de ponta a ponta
antes da integração com o provedor de identidade (Google / Microsoft OIDC).
Não valida credenciais reais — não usar em produção sem substituição.
"""

from __future__ import annotations

from fastapi import APIRouter, Body

from apps.api.core.security import create_access_token
from packages.domain.auth.models import RoleUsuario

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/token",
    summary="Login provisório (mock)",
    description=(
        "Gera um JWT assinado para o email e role indicados. "
        "Provisório — sem validação de senha. "
        "Será substituído pela integração Google/Microsoft OIDC."
    ),
)
def login(
    email: str = Body(..., embed=True, description="Email do utilizador."),
    role: RoleUsuario = Body(
        RoleUsuario.ENGENHEIRO,
        embed=True,
        description="Perfil de acesso (ADMIN, ENGENHEIRO ou CONVIDADO).",
    ),
) -> dict[str, str]:
    """Devolve access_token JWT assinado com sub=email e role=role."""
    token = create_access_token(email=email, role=role)
    return {"access_token": token, "token_type": "bearer"}
