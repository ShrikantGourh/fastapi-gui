import pytest

from tests.conftest import request_with_fallback


@pytest.mark.asyncio
async def test_create_and_execute_workflow_with_data_flow(client, endpoints, auth_headers):
    workflow = {
        "name": "order_enrichment",
        "steps": [
            {"id": "extract", "type": "transform", "config": {"set": {"order_id": "ord-9"}}},
            {
                "id": "enrich",
                "type": "transform",
                "input": "extract",
                "config": {"set": {"status": "validated"}},
            },
        ],
    }

    created = await request_with_fallback(
        client,
        "POST",
        endpoints.create_workflow,
        json=workflow,
        headers=auth_headers,
    )
    assert created.status_code in {200, 201}

    workflow_id = created.json().get("id") or created.json().get("workflow_id")
    assert workflow_id

    execution_paths = tuple(path.format(workflow_id=workflow_id) for path in endpoints.execute_workflow)
    executed = await request_with_fallback(
        client,
        "POST",
        execution_paths,
        json={"input": {"customer_id": "c1"}},
        headers=auth_headers,
    )
    assert executed.status_code == 200

    body = executed.json()
    output = body.get("output", body.get("result", body))
    assert output.get("order_id") == "ord-9"
    assert output.get("status") == "validated"


@pytest.mark.asyncio
async def test_workflow_step_failure_returns_error(client, endpoints, auth_headers):
    workflow = {
        "name": "failing_workflow",
        "steps": [
            {"id": "ok", "type": "transform", "config": {"set": {"x": 1}}},
            {"id": "boom", "type": "custom", "config": {"raise_error": True}},
        ],
    }

    created = await request_with_fallback(
        client,
        "POST",
        endpoints.create_workflow,
        json=workflow,
        headers=auth_headers,
    )
    assert created.status_code in {200, 201}

    workflow_id = created.json().get("id") or created.json().get("workflow_id")
    execution_paths = tuple(path.format(workflow_id=workflow_id) for path in endpoints.execute_workflow)

    failed = await request_with_fallback(
        client,
        "POST",
        execution_paths,
        json={"input": {}},
        headers=auth_headers,
        expected_non_404=False,
    )

    assert failed.status_code in {400, 422, 500}
    assert any(key in failed.json() for key in {"error", "detail", "message"})
