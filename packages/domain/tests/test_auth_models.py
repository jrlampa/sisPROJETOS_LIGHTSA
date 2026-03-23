"""Testes das entidades de autenticacao e autorizacao."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.domain.auth import RoleUsuario, Usuario


def test_usuario_cria_identidade_autenticada_valida() -> None:
    usuario = Usuario(
        email="engenharia@light.com",
        nome="Equipe Tecnica",
        role=RoleUsuario.ENGENHEIRO,
    )

    assert usuario.email == "engenharia@light.com"
    assert usuario.nome == "Equipe Tecnica"
    assert usuario.role is RoleUsuario.ENGENHEIRO
    assert usuario.id is not None


def test_usuario_rejeita_role_invalida() -> None:
    with pytest.raises(ValidationError):
        Usuario(
            email="guest@light.com",
            nome="Convidado",
            role="OPERADOR",
        )


def test_usuario_e_imutavel() -> None:
    usuario = Usuario(
        email="admin@light.com",
        nome="Administrador",
        role=RoleUsuario.ADMIN,
    )

    with pytest.raises(Exception):
        usuario.nome = "Outro Nome"  # type: ignore[misc]
