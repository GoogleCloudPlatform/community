FROM php-nginx:7.3-fpm-alpine

ARG source=/html

ENV DB_SERVER="mysql" \
    DB_NAME=prestashop \
    DB_USER=root \
    DB_PASSWD=admin

# copy nginx config 
COPY config/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

# make the root writable
RUN chmod a+wr /var/www/html

# copy sources
COPY $source /var/www/html

COPY config/docker_run.sh /bin/docker_run.sh

CMD ["docker_run.sh"]
