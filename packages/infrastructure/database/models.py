"""Mapeamentos ORM para persistencia local-first do projeto e auditoria."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
    cqt_analises: Mapped[list["CQTAnaliseORM"]] = relationship(
        back_populates="projeto", cascade="all, delete-orphan"
    )
    geometria_cad: Mapped["GeometriaProjetoORM | None"] = relationship(
        back_populates="projeto", uselist=False, cascade="all, delete-orphan"
    )
    postes_tracao: Mapped[list["PosteTracaoORM"]] = relationship(
        back_populates="projeto", cascade="all, delete-orphan"
    )


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


class CQTAnaliseORM(Base):
    """Representacao persistente da analise CQT associada a um projeto."""

    __tablename__ = "cqt_analises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    projeto_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo_projeto: Mapped[str] = mapped_column(String(40), nullable=False)
    recuperacao_clandestino_confirmada: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    quantidade_ligacoes_irregulares: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recebeu_leitura_trafo_maxima: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrente_trafo_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    carga_maxima_transformador_kva: Mapped[float | None] = mapped_column(Float, nullable=True)
    limite_carregamento_trafo_percent: Mapped[float] = mapped_column(Float, nullable=False)
    trafo_dentro_do_limite: Mapped[bool] = mapped_column(Boolean, nullable=False)
    qdt_total_dentro_do_limite: Mapped[bool] = mapped_column(Boolean, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    projeto: Mapped[ProjetoORM] = relationship(back_populates="cqt_analises")
    centro_carga: Mapped["CentroCargaORM"] = relationship(
        back_populates="cqt_analise", uselist=False, cascade="all, delete-orphan"
    )


class CentroCargaORM(Base):
    """Representacao persistente do centro de carga da analise CQT."""

    __tablename__ = "centros_carga"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    cqt_analise_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cqt_analises.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    queda_total_percent: Mapped[float] = mapped_column(Float, nullable=False)
    possui_erro_02: Mapped[bool] = mapped_column(Boolean, nullable=False)

    cqt_analise: Mapped[CQTAnaliseORM] = relationship(back_populates="centro_carga")
    transformador: Mapped["TransformadorORM"] = relationship(
        back_populates="centro_carga", uselist=False, cascade="all, delete-orphan"
    )
    trechos: Mapped[list["TrechoEletricoORM"]] = relationship(
        back_populates="centro_carga", cascade="all, delete-orphan"
    )


class TransformadorORM(Base):
    """Representacao persistente do transformador associado ao centro de carga."""

    __tablename__ = "transformadores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    centro_carga_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("centros_carga.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    descricao: Mapped[str] = mapped_column(String(120), nullable=False)
    potencia_nominal_kva: Mapped[float] = mapped_column(Float, nullable=False)
    carga_maxima_lida_kva: Mapped[float] = mapped_column(Float, nullable=False)
    corrente_lida_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    fator_carga_percent: Mapped[float] = mapped_column(Float, nullable=False)

    centro_carga: Mapped[CentroCargaORM] = relationship(back_populates="transformador")


class CondutorORM(Base):
    """Representacao persistente do condutor utilizado em um trecho eletrico."""

    __tablename__ = "condutores"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    resistencia_ohm_km: Mapped[float] = mapped_column(Float, nullable=False)
    ampacidade_a: Mapped[float] = mapped_column(Float, nullable=False)

    trechos: Mapped[list["TrechoEletricoORM"]] = relationship(back_populates="condutor")


class TrechoEletricoORM(Base):
    """Representacao persistente de cada trecho calculado na analise CQT."""

    __tablename__ = "trechos_eletricos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    centro_carga_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("centros_carga.id", ondelete="CASCADE"), nullable=False, index=True
    )
    condutor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("condutores.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo_rede: Mapped[str] = mapped_column(String(20), nullable=False)
    fases: Mapped[int] = mapped_column(Integer, nullable=False)
    comprimento_m: Mapped[float] = mapped_column(Float, nullable=False)
    corrente_a: Mapped[float] = mapped_column(Float, nullable=False)
    tensao_nominal_v: Mapped[float] = mapped_column(Float, nullable=False)
    ordem_no_circuito: Mapped[int] = mapped_column(Integer, nullable=False)
    consumidores_montante: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consumidores_jusante: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fases_montante: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fases_jusante: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resistencia_total_ohm: Mapped[float] = mapped_column(Float, nullable=False)
    queda_tensao_v: Mapped[float] = mapped_column(Float, nullable=False)
    queda_tensao_percent: Mapped[float] = mapped_column(Float, nullable=False)
    limite_qdt_percent: Mapped[float] = mapped_column(Float, nullable=False)
    dentro_do_limite_qdt: Mapped[bool] = mapped_column(Boolean, nullable=False)
    possui_erro_02: Mapped[bool] = mapped_column(Boolean, nullable=False)

    centro_carga: Mapped[CentroCargaORM] = relationship(back_populates="trechos")
    condutor: Mapped[CondutorORM] = relationship(back_populates="trechos")


class PosteTracaoORM(Base):
    """Representacao persistente do poste com os vaos de tracao em JSON."""

    __tablename__ = "postes_tracao"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    projeto_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    codigo: Mapped[str] = mapped_column(String(50), nullable=False)
    resistencia_nominal_daN: Mapped[float] = mapped_column(Float, nullable=False)
    vaos_json: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    projeto: Mapped[ProjetoORM] = relationship(back_populates="postes_tracao")
    resultado: Mapped["ResultadoTracaoORM"] = relationship(
        back_populates="poste", uselist=False, cascade="all, delete-orphan"
    )


class ResultadoTracaoORM(Base):
    """Representacao persistente do resultado mecanico calculado para um poste."""

    __tablename__ = "resultados_tracao"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    poste_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("postes_tracao.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    esforco_resultante_daN: Mapped[float] = mapped_column(Float, nullable=False)
    percentual_carregamento: Mapped[float] = mapped_column(Float, nullable=False)
    estado_mecanico: Mapped[str] = mapped_column(String(20), nullable=False)
    calculado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    poste: Mapped[PosteTracaoORM] = relationship(back_populates="resultado")


class GeometriaProjetoORM(Base):
    """Persistencia da geometria CAD 2.5D extraida de um ficheiro DXF.

    As coordenadas dos segmentos sao compactadas numa coluna JSON para evitar a
    criacao de milhares de registros relacionais de pontos, mantendo a performance
    de leitura/escrita sem sacrificar a rastreabilidade por projeto.
    """

    __tablename__ = "geometrias_projeto"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    projeto_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projetos.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    nome_arquivo: Mapped[str] = mapped_column(String(260), nullable=False)
    versao_dxf: Mapped[str] = mapped_column(String(20), nullable=False)
    dados_geometria: Mapped[list] = mapped_column(JSON, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    projeto: Mapped[ProjetoORM] = relationship(back_populates="geometria_cad")
