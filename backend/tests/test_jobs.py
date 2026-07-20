import time
from fastapi.testclient import TestClient
from app.main import app


def test_jobs_flow():
    # Context manager -> lifespan jalan -> scheduler start + seed default jobs
    with TestClient(app) as client:
        client.post("/api/v1/auth/register", json={"email": "job@example.com", "password": "rahasia123"})
        r = client.post("/api/v1/auth/login", json={"email": "job@example.com", "password": "rahasia123"})
        headers = {"Authorization": f"Bearer {r.json()['access_token']}"}

        # seed jobs kebentuk waktu startup
        r = client.get("/api/v1/jobs", headers=headers)
        assert r.status_code == 200
        jobs = r.json()
        assert any(j["name"] == "heartbeat" for j in jobs)
        hb = next(j for j in jobs if j["name"] == "heartbeat")
        assert hb["next_run"] is not None  # enabled -> ada jadwal berikutnya

        # run now -> history kecatat
        r = client.post(f"/api/v1/jobs/{hb['id']}/run", headers=headers)
        assert r.status_code == 202
        time.sleep(1.5)
        r = client.get(f"/api/v1/jobs/{hb['id']}/runs", headers=headers)
        assert r.status_code == 200
        runs = r.json()
        assert len(runs) >= 1
        assert runs[0]["status"] == "success"
        assert "alive" in runs[0]["output"]

        # cron invalid -> 422
        r = client.patch(f"/api/v1/jobs/{hb['id']}", json={"cron": "not-a-cron"}, headers=headers)
        assert r.status_code == 422

        # toggle off -> next_run hilang
        r = client.patch(f"/api/v1/jobs/{hb['id']}", json={"enabled": False}, headers=headers)
        assert r.status_code == 200
        assert r.json()["next_run"] is None

        # tanpa login -> 401
        r = client.get("/api/v1/jobs")
        assert r.status_code == 401
