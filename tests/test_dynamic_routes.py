import pytest

from tests.conftest import request_with_fallback


@pytest.mark.asyncio
async def test_dynamic_get_route_handles_query_params(client, endpoints, auth_headers):
    payload = {
        "name": "products_lookup",
        "path": "/dynamic/products",
        "method": "GET",
        "query_params": ["sku", "warehouse"],
        "response_template": {"sku": "{{sku}}", "warehouse": "{{warehouse}}"},
        "version": "v1",
    }

    response = await request_with_fallback(
        client, "POST", endpoints.create_api, json=payload, headers=auth_headers
    )
    assert response.status_code in {200, 201}

    created_path = response.json().get("path", payload["path"])
    call = await client.get(created_path, params={"sku": "sku-01", "warehouse": "west"})
    assert call.status_code == 200
    assert call.json().get("sku") == "sku-01"
    assert call.json().get("warehouse") == "west"


@pytest.mark.asyncio
async def test_dynamic_post_route_handles_json_body(client, endpoints, auth_headers):
    payload = {
        "name": "submit_ticket",
        "path": "/dynamic/tickets",
        "method": "POST",
        "body_schema": {
            "type": "object",
            "required": ["title", "priority"],
            "properties": {
                "title": {"type": "string"},
                "priority": {"type": "string"},
                "details": {"type": "string"},
            },
        },
        "response_template": {"ticket": "created", "title": "{{title}}", "priority": "{{priority}}"},
        "version": "v1",
    }

    response = await request_with_fallback(
        client, "POST", endpoints.create_api, json=payload, headers=auth_headers
    )
    assert response.status_code in {200, 201}

    body = {"title": "Login issue", "priority": "P1", "details": "Cannot login"}
    created_path = response.json().get("path", payload["path"])
    call = await client.post(created_path, json=body)

    assert call.status_code == 200
    data = call.json()
    assert data.get("title") == body["title"]
    assert data.get("priority") == body["priority"]
