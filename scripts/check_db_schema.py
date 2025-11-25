#!/usr/bin/env python3
"""Check actual Supabase database schema"""
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
    cur = conn.cursor()
    
    print("=" * 60)
    print("CHECKING DATABASE SCHEMA")
    print("=" * 60)
    
    # Check all tables in public schema
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"\n📋 Tables in public schema: {[t[0] for t in tables]}\n")
    
    # Check company table structure
    print("=" * 60)
    print("TABLE: public.company")
    print("=" * 60)
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'company'
        ORDER BY ordinal_position;
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<20} {row[1]:<20} NULL: {row[2]:<5} DEFAULT: {row[3]}")
    
    # Check match table structure
    print("\n" + "=" * 60)
    print("TABLE: public.match")
    print("=" * 60)
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'match'
        ORDER BY ordinal_position;
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<20} {row[1]:<20} NULL: {row[2]:<5} DEFAULT: {row[3]}")
    
    # Check if location_score exists
    cur.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'match' 
            AND column_name = 'location_score'
        );
    """)
    has_location_score = cur.fetchone()[0]
    print(f"\n{'✅' if has_location_score else '❌'} location_score column exists: {has_location_score}")
    
    cur.close()
    conn.close()
    print("\n" + "=" * 60)
    print("✅ Database connection successful")
    print("=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
