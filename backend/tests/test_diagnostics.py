def test_diagnostics_status(client):
    resp = client.get("/diagnostics/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "provider" in body["data"]
