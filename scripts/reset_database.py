#!/usr/bin/env python3
"""Reset database to correct schema"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in .env")
    sys.exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()
    
    print("=" * 60)
    print("⚠️  RESETTING DATABASE TO CORRECT SCHEMA")
    print("=" * 60)
    
    # Drop all existing tables
    print("\n🗑️  Dropping existing tables...")
    cur.execute("DROP TABLE IF EXISTS public.match CASCADE;")
    cur.execute("DROP TABLE IF EXISTS public.preferences CASCADE;")
    cur.execute("DROP TABLE IF EXISTS public.ground CASCADE;")
    cur.execute("DROP TABLE IF EXISTS public.client CASCADE;")
    cur.execute("DROP TABLE IF EXISTS public.company CASCADE;")
    cur.execute("DROP TYPE IF EXISTS match_status CASCADE;")
    print("✅ Old tables dropped")
    
    # Read and execute schema.sql
    print("\n📝 Creating new schema from db/schema.sql...")
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'schema.sql')
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    cur.execute(schema_sql)
    print("✅ Schema created")
    
    # Add location_score column (if not already in schema)
    print("\n📍 Adding location_score column to match table...")
    cur.execute("""
        ALTER TABLE public.match 
        ADD COLUMN IF NOT EXISTS location_score NUMERIC(5,2) NOT NULL DEFAULT 0 
        CHECK (location_score >= 0);
    """)
    print("✅ location_score column added")
    
    # Commit all changes
    conn.commit()
    
    # Verify new schema
    print("\n" + "=" * 60)
    print("VERIFYING NEW SCHEMA")
    print("=" * 60)
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'company'
        ORDER BY ordinal_position;
    """)
    print("\n📋 company columns:")
    for row in cur.fetchall():
        print(f"  - {row[0]:<20} {row[1]}")
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'match'
        ORDER BY ordinal_position;
    """)
    print("\n📋 match columns:")
    for row in cur.fetchall():
        print(f"  - {row[0]:<20} {row[1]}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ DATABASE RESET SUCCESSFUL!")
    print("=" * 60)
    print("\n💡 You can now run the app: python run.py")

except Exception as e:
    conn.rollback()
    print(f"\n❌ Error: {e}")
    sys.exit(1)
