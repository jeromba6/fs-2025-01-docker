FROM debian

RUN apt update; \
apt install nginx curl -y;

COPY nginx.conf /etc/nginx/nginx.conf
COPY static_content /var/www/html

ENTRYPOINT ["/usr/sbin/nginx"]
