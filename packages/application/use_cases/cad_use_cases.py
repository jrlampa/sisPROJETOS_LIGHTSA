"""Casos de uso da camada de aplicacao para o motor CAD 2.5D."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.cad.models import ArquivoDXF
from packages.infrastructure.adapters.dxf_adapter import EzdxfAdapter
from packages.infrastructure.repositories.cad_repository import CADRepository


class ImportarArquivoDxfUseCase:
    """Importa um ficheiro DXF do disco, extrai geometrias e persiste no projeto.

    Fluxo:
    1. O EzdxfAdapter le o ficheiro DXF e converte LINEs em entidades de dominio.
    2. O CADRepository serializa e persiste a GeometriaProjeto em JSON no SQLite.

    Separacao de responsabilidades:
    - O caso de uso apenas orquestra; nao conhece ezdxf nem SQLAlchemy.
    - O adaptador cuida da leitura do ficheiro fisico.
    - O repositorio cuida da persistencia.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        adapter: EzdxfAdapter | None = None,
        repository: CADRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._adapter = adapter
        self._repository = repository

    def executar(
        self,
        projeto_id: UUID,
        caminho_arquivo: str,
        nome_arquivo: str | None = None,
    ) -> ArquivoDXF:
        """Importa o DXF e persiste a geometria associada ao projeto.

        Args:
            projeto_id: UUID do projeto ao qual a geometria sera vinculada.
            caminho_arquivo: Caminho absoluto ou relativo para o ficheiro .dxf.
            nome_arquivo: Nome lógico a preservar no registro (ex.: nome original
                do upload). Quando None, usa o basename do caminho físico.

        Returns:
            ArquivoDXF com todas as geometrias extraidas.

        Raises:
            ValueError: Se o projeto_id nao corresponder a nenhum Projeto.
            FileNotFoundError: Se o ficheiro DXF nao for encontrado no disco.
        """
        adapter = self._adapter or EzdxfAdapter()
        arquivo_dxf: ArquivoDXF = adapter.ler_dxf(caminho_arquivo, nome_arquivo=nome_arquivo)

        with self._session_factory() as session:
            repository = self._repository or CADRepository(session)
            resultado = repository.salvar_geometria(projeto_id, arquivo_dxf)
            session.commit()

        return resultado
