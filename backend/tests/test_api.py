from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal, Base, engine
from backend.app.seed import seed_database

client = TestClient(app)

def setup_module(module):
    Base.metadata.create_all(bind=engine)
    seed_database(force_reseed=False)

def test_categories_endpoint():
    response = client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    slugs = [c["slug"] for c in data]
    assert "niche" in slugs
    assert "ai" in slugs
    assert "other" in slugs
    for cat in data:
        assert cat["total_reels"] > 0
        assert cat["reels_last_24h"] > 0

def test_category_stats_endpoint():
    response = client.get("/api/categories/ai/stats")
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "stats" in data
    assert data["stats"]["total_reels"] >= 100
    assert data["stats"]["reels_last_24h"] > 0
    assert data["stats"]["total_views"] > 0
    assert data["stats"]["fastest_growing"] is not None

def test_reels_last_24h_filter():
    response = client.get("/api/reels?category=ai&filter_mode=last_24h&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["category_name"] == "AI"
    assert data["filter_applied"] == "last_24h"
    assert len(data["items"]) > 0
    # Every item must have creator, metrics, and posted_at
    for item in data["items"]:
        assert item["creator"] is not None
        assert item["latest_metrics"] is not None
        assert item["latest_trending"] is not None
        assert item["latest_metrics"]["engagement_rate"] >= 0

def test_reels_fastest_growing_filter():
    response = client.get("/api/reels?category=niche&filter_mode=fastest_growing&limit=20")
    assert response.status_code == 200
    data = response.json()
    assert data["category_name"] == "Niche"
    assert data["filter_applied"] == "fastest_growing"
    items = data["items"]
    assert len(items) > 0
    # Check that growth velocity is descending
    velocities = [item["latest_trending"]["growth_velocity"] for item in items]
    for i in range(len(velocities) - 1):
        assert velocities[i] >= velocities[i+1]

def test_reels_top_100_filter():
    response = client.get("/api/reels?category=other&filter_mode=top_100&limit=100")
    assert response.status_code == 200
    data = response.json()
    assert data["category_name"] == "Other"
    assert len(data["items"]) == 100
    # Check that score is descending
    scores = [item["latest_trending"]["score"] for item in data["items"]]
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1]

def test_data_sources_endpoint():
    response = client.get("/api/data-sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 2
    types = [s["provider_type"] for s in sources]
    assert "mock_provider" in types
    assert "official_graph_api" in types

def test_data_sources_health():
    response = client.get("/api/data-sources/health")
    assert response.status_code == 200
    data = response.json()
    assert "healthy" in data
    assert "provider_type" in data
    assert "rate_limit" in data
