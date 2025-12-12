"""
Database migration script to add new columns for assignment requirements.
Adds: address, provider to ground table
Adds: type_score to match table
"""
import os
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

def migrate():
    """Apply schema updates to Supabase database."""
    print("🔄 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist before adding
        print("\n📋 Checking existing schema...")
        
        # Check client table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'client' AND table_schema = 'public'
        """)
        existing_client_cols = [row[0] for row in cursor.fetchall()]
        print(f"   Existing client columns: {', '.join(existing_client_cols)}")
        
        # Add location column to client if not exists
        if 'location' not in existing_client_cols:
            print("\n✅ Adding 'location' column to client table...")
            cursor.execute("""
                ALTER TABLE public.client 
                ADD COLUMN location VARCHAR(200)
            """)
            print("   ✓ location column added")
        else:
            print("\n⏭️  'location' column already exists in client table")
        
        # Check ground table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ground' AND table_schema = 'public'
        """)
        existing_ground_cols = [row[0] for row in cursor.fetchall()]
        print(f"\n   Existing ground columns: {', '.join(existing_ground_cols)}")

        # Add provider column if not exists
        if 'provider' not in existing_ground_cols:
            print("\n✅ Adding 'provider' column to ground table...")
            cursor.execute("""
                ALTER TABLE public.ground 
                ADD COLUMN provider VARCHAR(200)
            """)
            print("   ✓ provider column added")
        else:
            print("\n⏭️  'provider' column already exists")

        # Image storage: single image_url column maintained; photo_url no longer used
        
        # Check match table columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'match' AND table_schema = 'public'
        """)
        existing_match_cols = [row[0] for row in cursor.fetchall()]
        print(f"\n   Existing match columns: {', '.join(existing_match_cols)}")
        
        # Add type_score column if not exists
        if 'type_score' not in existing_match_cols:
            print("\n✅ Adding 'type_score' column to match table...")
            cursor.execute("""
                ALTER TABLE public.match 
                ADD COLUMN type_score NUMERIC DEFAULT 0
            """)
            print("   ✓ type_score column added")
        else:
            print("\n⏭️  'type_score' column already exists")
        
        # Create index on provider for faster ownership queries
        print("\n✅ Creating index on ground.provider...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ground_provider 
            ON public.ground(provider)
        """)
        print("   ✓ Index created")
        
        # Update match_status enum to include 'approved' if not exists
        print("\n✅ Checking match_status enum...")
        cursor.execute("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = 'match_status'::regtype
        """)
        existing_statuses = [row[0] for row in cursor.fetchall()]
        print(f"   Existing statuses: {', '.join(existing_statuses)}")
        
        if 'approved' not in existing_statuses:
            print("\n✅ Adding 'approved' status to match_status enum...")
            cursor.execute("""
                ALTER TYPE match_status ADD VALUE IF NOT EXISTS 'approved'
            """)
            print("   ✓ 'approved' status added")
        else:
            print("\n⏭️  'approved' status already exists")
        
        # Normalize existing statuses: accepted -> approved, rejected -> pending
        print("\n✅ Normalizing existing match statuses (accepted->approved, rejected->pending)...")
        try:
            cursor.execute("""
                UPDATE public.match 
                SET status = 'approved'::match_status 
                WHERE status::text = 'accepted'
            """)
            updated_accepted = cursor.rowcount
            cursor.execute("""
                UPDATE public.match 
                SET status = 'pending'::match_status 
                WHERE status::text = 'rejected'
            """)
            updated_rejected = cursor.rowcount
            print(f"   ✓ Updated {updated_accepted} accepted->approved, {updated_rejected} rejected->pending")
        except Exception as norm_e:
            print(f"   ⚠️  Status normalization skipped due to error: {norm_e}")
        
        # Commit all changes
        conn.commit()
        print("\n✅ ✅ ✅ Migration completed successfully! ✅ ✅ ✅")
        print("\n🚀 You can now use the application with all new features:")
        print("   • Photo upload for grounds")
        print("   • Address field (separate from location)")
        print("   • Ground ownership tracking (provider)")
        print("   • Match type scoring (0-100%)")
        print("   • Match approval workflow")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
        print("\n🔌 Database connection closed")

if __name__ == '__main__':
    migrate()
