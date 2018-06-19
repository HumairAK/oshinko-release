def test_root(client):
    resp = client.get('/')
    assert isinstance(resp.data, str)
    assert resp.status_code == 200
