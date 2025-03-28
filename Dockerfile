FROM python:3.13-slim

RUN apt update && apt install -y make curl libpq

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

RUN curl https://sh.rustup.rs -sSf | bash -s -- -y

RUN make setup

COPY python .

ENTRYPOINT ["uv", "run", "main.py"]