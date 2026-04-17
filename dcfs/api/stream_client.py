try:
    import requests
except Exception:  # pragma: no cover - optional runtime dependency
    requests = None


class StreamClient:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def send(self, event):
        if requests is None:
            raise RuntimeError("requests is required for HTTP streaming")
        response = requests.post(self.endpoint, json=event, timeout=2)
        response.raise_for_status()

