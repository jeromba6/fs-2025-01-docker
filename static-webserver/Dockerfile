FROM debian:12.10

RUN apt-get update; \
    apt-get install nginx/stable curl/stable --no-install-recommends -y; \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY static_content /var/www/html

ENTRYPOINT ["/usr/sbin/nginx"]
