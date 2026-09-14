"""Cliente HTTP assíncrono para a API de Dados Abertos da Câmara dos Deputados.

A API é pública e não exige chave de autenticação. Documentação:
https://dadosabertos.camara.leg.br/swagger/api.html
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
DEFAULT_TIMEOUT = 30.0
DEFAULT_BACKOFF_BASE = 0.5
MAX_ITENS = 100  # teto de itens por página aceito pela API


class CamaraAPIError(RuntimeError):
    """Erro ao consultar a API de Dados Abertos da Câmara."""


class CamaraClient:
    """Wrapper fino sobre httpx com paginação e retries.

    Pode ser usado como context manager assíncrono::

        async with CamaraClient() as client:
            dados = await client.get_all("/proposicoes", {"siglaTipo": "PEC"})
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        *,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
    ) -> None:
        self.base_url = (base_url or os.getenv("CAMARA_API_BASE") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout or float(os.getenv("HTTP_TIMEOUT", DEFAULT_TIMEOUT))
        self.backoff_base = backoff_base
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "CamaraClient":
        self._ensure_client()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={"Accept": "application/json"},
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _sleep(self, attempt: int) -> None:
        if self.backoff_base <= 0:
            return
        await asyncio.sleep(min(self.backoff_base * (2 ** attempt), 8.0))

    async def _request(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        retries: int = 3,
    ) -> dict[str, Any]:
        """Faz um GET, com retry/backoff em 429 e 5xx. Retorna o JSON completo."""
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        client = self._ensure_client()
        last_error: Exception | None = None

        for attempt in range(retries + 1):
            try:
                resp = await client.get(path, params=clean_params)
            except httpx.RequestError as exc:  # rede/timeout
                last_error = exc
                await self._sleep(attempt)
                continue

            if resp.status_code == 429 or resp.status_code >= 500:
                last_error = CamaraAPIError(f"HTTP {resp.status_code} ao consultar {path}")
                await self._sleep(attempt)
                continue

            if resp.status_code >= 400:
                raise CamaraAPIError(
                    f"HTTP {resp.status_code} ao consultar {path}: {resp.text[:200]}"
                )

            try:
                return resp.json()
            except ValueError as exc:
                raise CamaraAPIError(f"Resposta não-JSON de {path}") from exc

        raise CamaraAPIError(
            f"Falha ao consultar {path} após {retries + 1} tentativas: {last_error}"
        )

    async def get_dado(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Retorna o campo `dados` de um endpoint de detalhe (objeto único)."""
        payload = await self._request(path, params)
        return payload.get("dados")

    async def get_lista(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        max_itens: int | None = None,
    ) -> list[dict[str, Any]]:
        """Retorna a lista `dados` em uma única chamada, sem paginar.

        Usar para sub-recursos (ex.: `/proposicoes/{id}/tramitacoes`) que NÃO
        aceitam os parâmetros `pagina`/`itens` (a API responde 400) e já devolvem
        a coleção completa. Trunca no cliente se `max_itens` for informado.
        """
        payload = await self._request(path, params)
        dados = payload.get("dados") or []
        if max_itens is not None:
            return dados[:max_itens]
        return dados

    async def get_all(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        max_itens: int = 300,
    ) -> list[dict[str, Any]]:
        """Retorna a lista `dados`, paginando automaticamente até `max_itens`."""
        query: dict[str, Any] = dict(params or {})
        query.setdefault("itens", MAX_ITENS)
        pagina = int(query.get("pagina", 1))
        query["pagina"] = pagina

        resultados: list[dict[str, Any]] = []
        while True:
            payload = await self._request(path, query)
            dados = payload.get("dados") or []
            resultados.extend(dados)

            if len(resultados) >= max_itens:
                return resultados[:max_itens]

            tem_proxima = any(
                link.get("rel") == "next" for link in (payload.get("links") or [])
            )
            if not tem_proxima or not dados:
                break

            pagina += 1
            query["pagina"] = pagina

        return resultados
