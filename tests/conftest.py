import importlib
import os
from dataclasses import dataclass
from typing import Any, Iterable
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, Response


APP_IMPORT_CANDIDATES = [
    "app.main:app",
    "main:app",
    "src.main:app",
    "api.main:app",
]


@dataclass(frozen=True)
class EndpointMap:
    create_api: tuple[str, ...] = ("/apis", "/api", "/api-definitions")
    list_apis: tuple[str, ...] = ("/apis", "/api", "/api-definitions")
    version_api: tuple[str, ...] = (
        "/apis/{api_id}/versions",
        "/api-definitions/{api_id}/versions",
    )
    create_workflow: tuple[str, ...] = ("/workflows", "/workflow")
    execute_workflow: tuple[str, ...] = (
        "/workflows/{workflow_id}/execute",
        "/workflow/{workflow_id}/execute",
    )
    llm_endpoint: tuple[str, ...] = ("/llm/execute", "/llm", "/ai/execute")


def _load_app() -> Any:
    custom = os.getenv("TEST_APP_IMPORT")
    candidates = [custom] if custom else APP_IMPORT_CANDIDATES

    for candidate in [c for c in candidates if c]:
        module_name, app_name = candidate.split(":", maxsplit=1)
        try:
            module = importlib.import_module(module_name)
            return getattr(module, app_name)
        except (ImportError, AttributeError):
            continue

    raise RuntimeError(
        "Could not import FastAPI app. Set TEST_APP_IMPORT, e.g. TEST_APP_IMPORT=app.main:app"
    )


@pytest.fixture(scope="session")
def app() -> Any:
    return _load_app()


@pytest_asyncio.fixture
async def client(app: Any) -> Iterable[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture(scope="session")
def endpoints() -> EndpointMap:
    return EndpointMap()


async def request_with_fallback(
    client: AsyncClient,
    method: str,
    candidates: Iterable[str],
    *,
    expected_non_404: bool = True,
    **kwargs: Any,
) -> Response:
    last: Response | None = None
    for path in candidates:
        response = await client.request(method, path, **kwargs)
        last = response
        if response.status_code not in {404, 405}:
            return response

    if expected_non_404:
        raise AssertionError(
            f"No matching endpoint for {method}. Tried: {list(candidates)}. Last status: {last.status_code if last else 'none'}"
        )

    assert last is not None
    return last


@pytest.fixture
def dynamic_api_payload() -> dict[str, Any]:
    return {
        "name": "orders_lookup",
        "path": "/dynamic/orders",
        "method": "GET",
        "query_params": ["order_id"],
        "response_template": {"order_id": "{{order_id}}", "status": "ok"},
        "version": "v1",
    }


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer valid-jwt-token"}


@pytest.fixture
def mock_snowflake(monkeypatch: pytest.MonkeyPatch) -> dict[str, AsyncMock]:
    save_path = os.getenv("SNOWFLAKE_SAVE_PATH", "app.services.snowflake.save_record")
    load_path = os.getenv("SNOWFLAKE_LOAD_PATH", "app.services.snowflake.load_record")

    save_mock = AsyncMock(return_value={"ok": True})
    load_mock = AsyncMock(return_value={"id": "seed-1", "name": "orders_lookup"})

    monkeypatch.setattr(save_path, save_mock, raising=False)
    monkeypatch.setattr(load_path, load_mock, raising=False)
    return {"save": save_mock, "load": load_mock}


@pytest.fixture
def mock_llm(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    llm_path = os.getenv("LLM_INVOKE_PATH", "app.services.llm.invoke")
    llm_mock = AsyncMock(
        return_value='{"intent":"create_api","confidence":0.98,"result":{"name":"orders"}}'
    )
    monkeypatch.setattr(llm_path, llm_mock, raising=False)
    return llm_mock


@pytest.fixture
def mock_okta_jwks(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    jwks_path = os.getenv("OKTA_JWKS_VALIDATE_PATH", "app.auth.okta.validate_jwt")
    validate_mock = AsyncMock(return_value={"sub": "qa-user", "scope": "api:write"})
    monkeypatch.setattr(jwks_path, validate_mock, raising=False)
    return validate_mock
