import os
from supabase import create_client, Client
import os

url = os.getenv("SUPABASE_URL", "")
key = os.getenv("SUPABASE_KEY", "")
supabase: Client = create_client(url, key)

def setup_database():
    sql = """
    CREATE TABLE IF NOT EXISTS neuro_stats (
        id BIGINT PRIMARY KEY,
        dopamine FLOAT DEFAULT 0.5,
        serotonin FLOAT DEFAULT 0.5,
        norepinephrine FLOAT DEFAULT 0.2,
        oxytocin FLOAT DEFAULT 0.4,
        atp FLOAT DEFAULT 100.0,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    ALTER TABLE neuro_stats ENABLE ROW LEVEL SECURITY;

    DO $$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Allow anonymous read') THEN
            CREATE POLICY "Allow anonymous read" ON neuro_stats FOR SELECT USING (true);
        END IF;
    END $$;

    INSERT INTO neuro_stats (id, dopamine, serotonin, norepinephrine, oxytocin, atp)
    VALUES (1, 0.5, 0.5, 0.2, 0.4, 100.0)
    ON CONFLICT (id) DO NOTHING;
    """
    try:
        # Note: supabase-py doesn't have a direct 'rpc' for raw SQL unless configured in DB
        # We will try to update the table directly which will fail if it doesn't exist,
        # but the user can run the SQL in the dashboard.
        
        print("Please run the following SQL in your Supabase SQL Editor to initialize the table:")
        print(sql)
        
    except Exception as e:
        print(f"Setup Info: {e}")

if __name__ == "__main__":
    setup_database()
