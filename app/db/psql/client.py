import os
from typing import Self

import asyncpg
from asyncpg import Pool, Record
from dotenv import load_dotenv

load_dotenv()

type ARG_TYPE = str | bytes


class Psql:
    cache: Self | None = None

    def __new__(cls: type[Self]) -> Self:
        if not cls.cache:
            cls.cache = super().__new__(cls)

        return cls.cache

    def __init__(self: Self) -> None:
        self.pool: Pool

    async def __aenter__(self: Self) -> Self:
        self.pool = await asyncpg.create_pool(dsn=os.getenv("PSQL_URI"))
        return self

    async def __aexit__(self: Self, *_) -> None:  # noqa: ANN002
        await self.pool.close()

    async def close(self) -> None:
        await self.pool.close()

    async def execute(self: Self, query: str, *args: ARG_TYPE) -> None:
        await self.pool.execute(query, *args)

    async def fetch_row(self: Self, query: str, *args: ARG_TYPE) -> Record:
        return await self.pool.fetchrow(query, *args)
