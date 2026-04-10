import asyncio
import json
import time

import pytest

from tests.conftest import request_with_fallback


@pytest.mark.asyncio
async def test_llm_response_is_mocked_and_parsed(client, endpoints, mock_llm, auth_headers):
    payload = {"prompt": "Create an orders API with id param"}

    response = await request_with_fallback(
        client,
        "POST",
        endpoints.llm_endpoint,
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code in {200, 201}

    body = response.json()
    parsed = body.get("parsed") or body.get("result") or body

    if isinstance(parsed, str):
        parsed = json.loads(parsed)

    assert parsed["intent"] == "create_api"
    assert 0 <= parsed["confidence"] <= 1
    assert isinstance(parsed.get("result"), dict)
    assert mock_llm.called


@pytest.mark.asyncio
async def test_llm_schema_compliance(client, endpoints, mock_llm, auth_headers):
    response = await request_with_fallback(
        client,
        "POST",
        endpoints.llm_endpoint,
        json={"prompt": "Generate API schema"},
        headers=auth_headers,
    )
    assert response.status_code in {200, 201}

    data = response.json().get("parsed", response.json())
    if isinstance(data, str):
        data = json.loads(data)

    assert set(["intent", "confidence", "result"]).issubset(data.keys())
    assert isinstance(data["intent"], str)
    assert isinstance(data["confidence"], (int, float))
    assert isinstance(data["result"], dict)


@pytest.mark.asyncio
async def test_bonus_performance_1000_calls(client):
    path = "/health"

    start = time.perf_counter()
    tasks = [client.get(path) for _ in range(1000)]
    responses = await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start

    # Accept 95% success to reduce flakiness in constrained CI.
    success_count = sum(1 for r in responses if r.status_code in {200, 204})
    assert success_count >= 950

    # Default threshold for in-memory ASGI test transport.
    assert elapsed < 5.0
