FROM php:7.3-fpm-alpine

RUN apk update \
    && apk --no-cache add runit nginx \
    && mkdir -p /service \
    && rm -rf /var/cache/apk/*

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# install php extensions
RUN apk add --no-cache freetype libpng libjpeg-turbo freetype-dev libpng-dev \
              libjpeg-turbo-dev libmcrypt-dev icu-dev libxml2-dev libzip-dev \
    &&  docker-php-ext-configure gd \
        --with-gd \
        --with-freetype-dir=/usr/include/ \
        --with-png-dir=/usr/include/ \
        --with-jpeg-dir=/usr/include/ \
   &&  NPROC=$(grep -c ^processor /proc/cpuinfo 2>/dev/null || 1) && \
       docker-php-ext-install -j${NPROC} gd \
   && docker-php-ext-install iconv intl pdo_mysql mbstring soap zip \
   && apk del --no-cache freetype-dev libpng-dev libjpeg-turbo-dev

RUN docker-php-source extract \
  && if [ -d "/usr/src/php/ext/mysqli" ]; then docker-php-ext-install mysqli; fi \
  && if [ -d "/usr/src/php/ext/mcrypt" ]; then docker-php-ext-install mcrypt; fi \
	&& if [ -d "/usr/src/php/ext/opcache" ]; then docker-php-ext-install opcache; fi \
	&& docker-php-source delete


# configure runit
ADD config/etc/runit /etc/runit
ADD service /service

# configure nginx
ADD config/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
ADD config/nginx/nginx.conf /etc/nginx/nginx.conf

# configure php-fpm
ADD config/php/php.ini /usr/local/etc/php/php.ini
ADD config/php-fpm/php-fpm.d/www.conf /usr/local/etc/php-fpm.d/www.conf

EXPOSE 80/tcp

CMD ["/sbin/runit-init"]

