FROM python:3.13.1-slim-bookworm

COPY application /
RUN apt update && \
    apt upgrade -y && \
    apt install curl -y && \
    apt clean && \
    mkdir /data && \
    useradd -m -s /bin/bash workshop && \
    chown -R workshop:workshop /data

USER workshop

CMD [ "python", "-u", "/api-backend.py" ]