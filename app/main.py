import uvicorn
from fastapi import FastAPI
from lwe import Secret
from models.encrypt.inbound import EncryptIn
from models.encrypt.outbound import EncryptOut

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.post("/encrypt", response_model=EncryptOut)
async def encrypt(message: EncryptIn) -> EncryptOut:
    secret = Secret()
    public = secret.generate_public_key()
    return EncryptOut(encrypted=public.encrypt(message.message))


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
