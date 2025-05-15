FROM debian:12.10

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install python3.11-minimal/stable curl/stable -y --no-install-recommends && \
    apt-get clean
COPY application /
RUN mkdir /data && \
    useradd -m -s /bin/bash workshop && \
    chown -R workshop:workshop /data

USER workshop

CMD [ "python3", "-u", "/api_backend.py" ]