"""Entidade Usuario e enumeracao de roles para RBAC."""

from __future__ import annotations

from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class RoleUsuario(str, Enum):
    """Perfis de acesso do sistema.

    - ADMIN: acesso total (leitura + escrita + administração).
    - ENGENHEIRO: acesso de leitura e escrita de dados técnicos.
    - CONVIDADO: acesso apenas de leitura.
    """

    ADMIN = "ADMIN"
    ENGENHEIRO = "ENGENHEIRO"
    CONVIDADO = "CONVIDADO"


class Usuario(BaseModel):
    """Identidade autenticada carregada pelo JWT."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    email: str = Field(min_length=3)
    nome: str = Field(min_length=1)
    role: RoleUsuario
