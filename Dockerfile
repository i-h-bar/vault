FROM python:3.13-slim

RUN apt-get update && apt-get install -y make curl build-essential

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

ENV PATH=/home/user/.local/bin:$PATH
ENV PATH="/root/.cargo/bin:${PATH}"

COPY pyproject.toml uv.lock Cargo.toml Cargo.lock  ./
COPY src src
COPY app app

RUN make binary_docker

COPY app .

ENTRYPOINT ["uv", "run", "main.py", "--no-default-groups"]
