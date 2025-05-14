FROM debian

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install python3 curl -y && \
    apt-get clean
COPY application /
RUN mkdir /data && \
    useradd -m -s /bin/bash workshop && \
    chown -R workshop:workshop /data

USER workshop

CMD [ "python3", "-u", "/api-backend.py" ]