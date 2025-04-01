import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

pool = asyncpg.create_pool(dsn=os.getenv("PSQL_URI"))
