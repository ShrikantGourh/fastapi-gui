import pytest

from tests.conftest import request_with_fallback


@pytest.mark.asyncio
async def test_multiple_versions_route_correctly(client, endpoints, auth_headers):
    base = {
        "name": "pricing",
        "path": "/dynamic/pricing",
        "method": "GET",
        "query_params": ["sku"],
        "response_template": {"version": "v1", "sku": "{{sku}}"},
        "version": "v1",
    }

    create = await request_with_fallback(
        client, "POST", endpoints.create_api, json=base, headers=auth_headers
    )
    assert create.status_code in {200, 201}

    api_id = create.json().get("id") or create.json().get("api_id") or base["name"]

    v2_payload = {
        "version": "v2",
        "response_template": {"version": "v2", "sku": "{{sku}}", "discount": True},
    }

    version_paths = tuple(path.format(api_id=api_id) for path in endpoints.version_api)
    v2_response = await request_with_fallback(
        client, "POST", version_paths, json=v2_payload, headers=auth_headers
    )
    assert v2_response.status_code in {200, 201}

    path = create.json().get("path", base["path"])
    v1 = await client.get(f"{path}?version=v1&sku=sku-1")
    v2 = await client.get(f"{path}?version=v2&sku=sku-1")

    assert v1.status_code == 200
    assert v2.status_code == 200
    assert v1.json().get("version") == "v1"
    assert v2.json().get("version") == "v2"


@pytest.mark.asyncio
async def test_latest_version_is_default_fallback(client, endpoints, auth_headers):
    payload = {
        "name": "inventory",
        "path": "/dynamic/inventory",
        "method": "GET",
        "query_params": ["sku"],
        "response_template": {"version": "v1", "sku": "{{sku}}", "qty": 5},
        "version": "v1",
    }
    created = await request_with_fallback(
        client, "POST", endpoints.create_api, json=payload, headers=auth_headers
    )
    assert created.status_code in {200, 201}

    api_id = created.json().get("id") or created.json().get("api_id") or payload["name"]
    version_paths = tuple(path.format(api_id=api_id) for path in endpoints.version_api)

    await request_with_fallback(
        client,
        "POST",
        version_paths,
        json={"version": "v2", "response_template": {"version": "v2", "sku": "{{sku}}", "qty": 99}},
        headers=auth_headers,
    )

    path = created.json().get("path", payload["path"])
    latest = await client.get(path, params={"sku": "sku-2"})
    assert latest.status_code == 200
    assert latest.json().get("version") == "v2"
