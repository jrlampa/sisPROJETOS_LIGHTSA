"""Casos de uso da camada de aplicacao para o motor de tracao poste a poste."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.tracao.models import Poste, ResultadoTracao, Vao
from packages.infrastructure.repositories.tracao_repository import TracaoRepository


class CalcularTracaoProjetoUseCase:
    """Calcula e persiste resultados mecanicos de tracao para um projeto.

    Fluxo:
    1. Valida os dados brutos de cada poste via modelos de dominio (Poste/Vao).
    2. Calcula ResultadoTracao para cada poste usando as regras vetoriais do dominio.
    3. Persiste postes e resultados no repositório de infraestrutura.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        repository: TracaoRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository

    def executar(self, projeto_id: UUID, dados_brutos_postes: list[dict]) -> list[ResultadoTracao]:
        """Calcula a tracao de todos os postes e salva os resultados."""
        postes: list[Poste] = []
        resultados: list[ResultadoTracao] = []

        for dados_poste in dados_brutos_postes:
            vaos = tuple(Vao.model_validate(vao) for vao in dados_poste.get("vaos", []))
            payload_poste = {
                "codigo": dados_poste["codigo"],
                "resistencia_nominal_daN": dados_poste["resistencia_nominal_daN"],
                "vaos": vaos,
            }
            if "id" in dados_poste:
                payload_poste["id"] = dados_poste["id"]

            poste = Poste.model_validate(payload_poste)
            resultado = ResultadoTracao.calcular(poste)

            postes.append(poste)
            resultados.append(resultado)

        with self._session_factory() as session:
            repository = self._repository or TracaoRepository(session)
            repository.salvar_resultados_tracao(
                projeto_id,
                list(zip(postes, resultados, strict=True)),
            )
            session.commit()

        return resultados
