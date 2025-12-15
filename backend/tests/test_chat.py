def test_chat_ok(client):
    resp = client.post("/chat/", json={"question": "Explique ICP."})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert "data" in body
    # Em modo teste, a resposta será um mock com estrutura de dict
    data = body["data"]
    assert isinstance(data, dict)
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0


def test_chat_empty_question(client):
    resp = client.post("/chat/", json={"question": ""})
    assert resp.status_code in (400, 422)
