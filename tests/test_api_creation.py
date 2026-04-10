import pytest

from tests.conftest import request_with_fallback


@pytest.mark.asyncio
async def test_create_dynamic_api_and_execute(
    client, endpoints, dynamic_api_payload, mock_snowflake, auth_headers
):
    create_response = await request_with_fallback(
        client,
        "POST",
        endpoints.create_api,
        json=dynamic_api_payload,
        headers=auth_headers,
    )
    assert create_response.status_code in {200, 201}

    created = create_response.json()
    assert any(key in created for key in {"id", "api_id", "name", "path"})

    route_path = created.get("path") or dynamic_api_payload["path"]
    execute_response = await client.get(route_path, params={"order_id": "ord-1001"})
    assert execute_response.status_code == 200

    body = execute_response.json()
    assert body.get("order_id") == "ord-1001"

    assert mock_snowflake["save"].called or mock_snowflake["load"].called


@pytest.mark.asyncio
async def test_created_api_is_listed(client, endpoints, dynamic_api_payload, auth_headers):
    await request_with_fallback(
        client,
        "POST",
        endpoints.create_api,
        json=dynamic_api_payload,
        headers=auth_headers,
    )

    list_response = await request_with_fallback(client, "GET", endpoints.list_apis, headers=auth_headers)
    assert list_response.status_code == 200

    payload = list_response.json()
    apis = payload if isinstance(payload, list) else payload.get("items", payload.get("data", []))
    assert any(
        dynamic_api_payload["name"] in str(item.get("name", ""))
        or dynamic_api_payload["path"] in str(item.get("path", ""))
        for item in apis
    )
