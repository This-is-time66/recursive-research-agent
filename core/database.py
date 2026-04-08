import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

NEON_DATABASE_URL = os.environ.get("NEON_DATABASE_URL")


def db_execute(query: str, params=None, fetch: str = None):
    """
    Execute a SQL query against the Neon Postgres database.
    fetch: 'one' | 'all' | 'returning' | None
    """
    conn = psycopg2.connect(
        NEON_DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if fetch == "one":
                    return cur.fetchone()
                elif fetch == "all":
                    return cur.fetchall()
                elif fetch == "returning":
                    return cur.fetchone()
    finally:
        conn.close()