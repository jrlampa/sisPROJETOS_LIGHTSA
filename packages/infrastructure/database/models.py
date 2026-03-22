"""Mapeamentos ORM para persistencia local-first do projeto e auditoria."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarativa do SQLAlchemy para a camada de infraestrutura."""


class ProjetoORM(Base):
    """Representacao persistente do projeto para armazenamento local-first."""

    __tablename__ = "projetos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    codigo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    localidade: Mapped[str] = mapped_column(String(200), nullable=False)
    etapa_atual: Mapped[str] = mapped_column(String(40), nullable=False)
    checklist_triagem: Mapped[dict] = mapped_column(JSON, nullable=False)
    evidencias: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class HistoricoAuditoriaORM(Base):
    """Representacao persistente dos eventos de auditoria do workflow."""

    __tablename__ = "historico_auditoria"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    projeto_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    etapa_origem: Mapped[str | None] = mapped_column(String(40), nullable=True)
    etapa_destino: Mapped[str] = mapped_column(String(40), nullable=False)
    acao: Mapped[str] = mapped_column(String(200), nullable=False)
    responsavel: Mapped[str] = mapped_column(String(120), nullable=False)
    justificativa: Mapped[str | None] = mapped_column(Text, nullable=True)
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
