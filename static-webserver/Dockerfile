FROM debian

RUN apt-get update; \
apt-get install nginx curl -y;

COPY nginx.conf /etc/nginx/nginx.conf
COPY static_content /var/www/html

ENTRYPOINT ["/usr/sbin/nginx"]
