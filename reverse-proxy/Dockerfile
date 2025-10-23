FROM debian:12.10

RUN apt-get update; \
    apt-get install nginx/oldstable curl/oldstable openssl/oldstable --no-install-recommends -y; \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /etc/nginx/ssl

COPY nginx.conf /etc/nginx/nginx.conf
COPY startup.sh /usr/local/bin/startup.sh

ENTRYPOINT ["/usr/local/bin/startup.sh"]
