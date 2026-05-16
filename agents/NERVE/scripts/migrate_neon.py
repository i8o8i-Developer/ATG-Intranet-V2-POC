import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL missing from .env")
    exit(1)

async def run_migration():
    print("Connecting to Neon DB...")
    conn = await asyncpg.connect(DATABASE_URL)
    print("Connected! Reading schema file...")
    
    with open("migrations/001_nerve_schema.sql", "r") as f:
        schema_sql = f.read()
        
    print("Executing schema...")
    await conn.execute(schema_sql)
    print("Schema deployed successfully to Neon DB!")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
