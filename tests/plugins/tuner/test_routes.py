"""Integration tests for HTTP file-serving routes and path traversal guards."""

import pytest


class TestFileServing:
    def test_get_yin_worker_returns_js(self, client):
        r = client.get("/api/plugins/tuner/workers/yin.js")
        assert r.status_code == 200
        assert "yinDetect" in r.text
        assert r.headers["content-type"].startswith("application/javascript")

    def test_get_nonexistent_worker_returns_404(self, client):
        assert client.get("/api/plugins/tuner/workers/nonexistent.js").status_code == 404

    def test_get_nonexistent_viz_returns_404(self, client):
        assert client.get("/api/plugins/tuner/visualization/nonexistent.js").status_code == 404

    def test_get_nonexistent_utils_returns_404(self, client):
        assert client.get("/api/plugins/tuner/utils/nonexistent.js").status_code == 404


class TestPathTraversal:
    def test_worker_path_traversal_blocked(self, client):
        assert client.get("/api/plugins/tuner/workers/../routes.py").status_code in (404, 422)

    def test_viz_path_traversal_blocked(self, client):
        assert client.get("/api/plugins/tuner/visualization/../routes.py").status_code in (404, 422)

    def test_utils_path_traversal_blocked(self, client):
        assert client.get("/api/plugins/tuner/utils/../routes.py").status_code in (404, 422)


class TestConfigEndpoint:
    def test_post_returns_ok(self, client):
        r = client.post("/api/plugins/tuner/config", json={"lastTuning": "Drop D"})
        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_get_config_status_200(self, client):
        assert client.get("/api/plugins/tuner/config").status_code == 200
