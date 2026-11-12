import murmur.http as h


class FakeResp:
    def __init__(self, status=200, content=b"{}", headers=None):
        self.status_code, self.content, self.headers = status, content, headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise h.requests.HTTPError(str(self.status_code))

    def json(self):
        import json

        return json.loads(self.content)


def test_backs_off_on_rate_limit_then_succeeds(monkeypatch):
    client = h.PoliteClient()
    responses = iter(
        [FakeResp(200, b"Please limit requests to one every 5 seconds"), FakeResp(200, b'{"ok": 1}')]
    )
    monkeypatch.setattr(client.session, "get", lambda *a, **k: next(responses))
    slept = []
    monkeypatch.setattr(h.time, "sleep", slept.append)
    assert client.get_json("https://api.gdeltproject.org/x") == {"ok": 1}
    assert slept == [h.RATE_LIMIT_BACKOFF]


def test_gives_up_quietly_after_retries(monkeypatch):
    client = h.PoliteClient()
    monkeypatch.setattr(client.session, "get", lambda *a, **k: FakeResp(429, b""))
    monkeypatch.setattr(h.time, "sleep", lambda s: None)
    assert client.get_json("https://example.com/x") is None
