import json

import asyncpg
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from lwe import Public, Secret
from models.output import EncryptedOutput
from models.session.inbound import SessionIn
from redis.asyncio import Redis

pool = asyncpg.create_pool()
redis = Redis()
app = FastAPI()


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World!"}


@app.post("/session")
async def session(session_in: SessionIn, request: Request) -> EncryptedOutput | HTTPException:
    client_public_key_b64 = session_in.pub_key
    client_public_key = Public.from_b64(client_public_key_b64)

    if client := request.client:
        client_ip = client.host
    else:
        return HTTPException(status_code=400, detail="Client not found")

    app_secret = Secret()
    app_public_key = app_secret.generate_public_key().to_b64()
    app_public_key_encrypted = client_public_key.encrypt(app_public_key)

    redis_keys = {
        "secret": app_secret.to_b64(),
        "public": client_public_key_b64,
    }

    await redis.set(client_ip, json.dumps(redis_keys), ex=1800)

    return EncryptedOutput(content=app_public_key_encrypted)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
