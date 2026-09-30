import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import logging
from backend.app.database import engine, SessionLocal, Base
from backend.app.models.category import Category
from backend.app.models.data_source import DataSource
from backend.app.models.creator import Creator
from backend.app.models.reel import Reel
from backend.app.models.reel_metrics import ReelMetrics
from backend.app.models.trending_score import TrendingScore
from backend.app.data_sources.service import DataSourceService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

INITIAL_CATEGORIES = [
    {
        "name": "Niche",
        "slug": "niche",
        "description": "Latest in tech: breakthrough websites, secret web apps, iOS/Android mobile apps, new devices & viral tech trends.",
        "icon": "sparkles",
        "color": "#8B5CF6" # Violet
    },
    {
        "name": "AI",
        "slug": "ai",
        "description": "Mind-blowing AI tools, crazy photo-to-prompt tricks, Midjourney/Flux prompts, talking video avatars & model breakthroughs.",
        "icon": "cpu",
        "color": "#3B82F6" # Blue
    },
    {
        "name": "Other",
        "slug": "other",
        "description": "Tech-adjacent trends, viral prompt lifestyle hacks, developer comedy, and creative media gaining massive popularity.",
        "icon": "globe",
        "color": "#EC4899" # Pink
    },
    {
        "name": "Blockchain",
        "slug": "blockchain",
        "description": "Web3 innovations, Solidity smart contracts, DeFi architectures, ZK-rollups, and roadmaps to land a blockchain job as a fresher.",
        "icon": "blocks",
        "color": "#10B981" # Emerald
    }
]

INITIAL_DATA_SOURCES = [
    {
        "name": "Apify Instagram Reels (Live Cloud Ingestion)",
        "provider_type": "apify_provider",
        "auth_type": "api_key",
        "is_active": True,
        "config_json": '{"api_token": "", "actor_id": "apify~instagram-reel-scraper"}',
        "status_message": "Ready - Paste Apify API Token to pull live real reels"
    },
    {
        "name": "Permitted Sandbox Feed (Mock / Seed Provider)",
        "provider_type": "mock_provider",
        "auth_type": "none",
        "is_active": False,
        "config_json": "{}",
        "status_message": "Standby - Mock provider"
    },
    {
        "name": "Meta Instagram Graph API (Official)",
        "provider_type": "official_graph_api",
        "auth_type": "oauth2_bearer",
        "is_active": False,
        "config_json": '{"access_token": "", "account_id": ""}',
        "status_message": "Available - Configure credentials to connect live Meta account"
    }
]

def seed_database(force_reseed: bool = False):
    logger.info("Initializing database schema...")
    if force_reseed:
        logger.info("Dropping existing tables to align schema...")
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Categories
        for cat_data in INITIAL_CATEGORIES:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing:
                cat = Category(**cat_data)
                db.add(cat)
                logger.info(f"Created category: {cat_data['name']}")
            else:
                existing.description = cat_data["description"]
                existing.color = cat_data["color"]
                existing.icon = cat_data["icon"]
        db.commit()

        # 2. Seed Data Sources
        for ds_data in INITIAL_DATA_SOURCES:
            existing = db.query(DataSource).filter(DataSource.provider_type == ds_data["provider_type"]).first()
            if not existing:
                ds = DataSource(**ds_data)
                db.add(ds)
                logger.info(f"Created data source: {ds_data['name']}")
        db.commit()

        # Only inject mock reels if force_reseed is explicitly requested AND active source is mock
        active_source = db.query(DataSource).filter(DataSource.is_active == True).first()
        if force_reseed and active_source and active_source.provider_type == "mock_provider":
            categories = db.query(Category).all()
            for cat in categories:
                DataSourceService.sync_category(db, cat, data_source=active_source, limit=50)

        logger.info("Database schema setup complete.")
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database(force_reseed=False)
