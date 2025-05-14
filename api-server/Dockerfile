FROM debian

RUN apt update && \
    apt upgrade -y && \
    apt install python3 curl -y && \
    apt clean
COPY application /
RUN mkdir /data && \
    useradd -m -s /bin/bash workshop && \
    chown -R workshop:workshop /data

USER workshop

CMD [ "python3", "-u", "/api-backend.py" ]