"""
Phase 4 Migration: Multi-Vertical & Partner Mode
Creates Partner, Vertical, and MethodProfile tables.

Usage:
    python backend/scripts/migrations/20260108_phase4_multi_vertical.py --up
    python backend/scripts/migrations/20260108_phase4_multi_vertical.py --down
"""

import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.config import settings


def migrate_up(engine):
    """Apply Phase 4 schema changes."""
    with engine.connect() as conn:
        # Create partners table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS partners (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                language_tone TEXT NOT NULL DEFAULT 'consultative',
                default_method_version TEXT NOT NULL DEFAULT '1.0',
                feature_overrides TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create verticals table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS verticals (
                id TEXT PRIMARY KEY,
                partner_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                available_templates TEXT,
                governance_gates_ref TEXT,
                risk_rules_ref TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE CASCADE,
                UNIQUE (partner_id, name)
            )
        """))
        
        # Create method_profiles table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS method_profiles (
                id TEXT PRIMARY KEY,
                partner_id TEXT NOT NULL,
                vertical_id TEXT,
                method_version TEXT NOT NULL DEFAULT '1.0',
                effective_language_tone TEXT NOT NULL,
                template_customizations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES partners(id) ON DELETE CASCADE,
                FOREIGN KEY (vertical_id) REFERENCES verticals(id) ON DELETE CASCADE,
                UNIQUE (partner_id, vertical_id, method_version)
            )
        """))
        
        # Create indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_verticals_partner ON verticals(partner_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_method_profiles_partner ON method_profiles(partner_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_method_profiles_vertical ON method_profiles(vertical_id)"))
        
        # Seed default FCJ partner
        conn.execute(text("""
            INSERT OR IGNORE INTO partners (id, name, description, language_tone, default_method_version, feature_overrides)
            VALUES (
                'fcj_default',
                'Founder Challenge Journey',
                'Default TR4CTION method for all clients without custom partner configuration',
                'consultative',
                '1.0',
                '{}'
            )
        """))
        
        conn.commit()
        print("✅ Phase 4 schema created successfully")
        print("✅ Default FCJ partner seeded")


def migrate_down(engine):
    """Rollback Phase 4 schema changes."""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS method_profiles"))
        conn.execute(text("DROP TABLE IF EXISTS verticals"))
        conn.execute(text("DROP TABLE IF EXISTS partners"))
        conn.commit()
        print("✅ Phase 4 schema rolled back")


def main():
    parser = argparse.ArgumentParser(description="Phase 4 Multi-Vertical Migration")
    parser.add_argument(
        "--up",
        action="store_true",
        help="Apply migration (create tables)"
    )
    parser.add_argument(
        "--down",
        action="store_true",
        help="Rollback migration (drop tables)"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        default=None,
        help="Override database URL (defaults to settings.DATABASE_URL)"
    )
    
    args = parser.parse_args()
    
    if not args.up and not args.down:
        parser.error("Must specify --up or --down")
    
    # Get database URL
    database_url = args.database_url or settings.DATABASE_URL
    if not database_url:
        print("❌ DATABASE_URL not configured")
        sys.exit(1)
    
    # Create engine
    engine = create_engine(database_url)
    
    try:
        if args.up:
            migrate_up(engine)
        elif args.down:
            migrate_down(engine)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
