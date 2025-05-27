FROM debian:12.10

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install python3/stable curl/stable --no-install-recommends -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY application /
RUN mkdir /data && \
    useradd -m -s /bin/bash workshop && \
    chown -R workshop:workshop /data

USER workshop

CMD [ "python3", "-u", "/api_backend.py" ]
lskdjf