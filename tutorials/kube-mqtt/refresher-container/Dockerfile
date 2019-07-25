FROM python:3.7-alpine as base
FROM base as builder
RUN mkdir /install
WORKDIR /install
RUN apk add --no-cache \
        libressl-dev \
        musl-dev \
        libffi-dev \
        build-base \
        openssl-dev
COPY requirements.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt
FROM base
RUN apk add --update bash && rm -rf /var/cache/apk/*
COPY --from=builder /install /usr/local
COPY src /app
WORKDIR /app
CMD ["/usr/local/bin/python", "run_bridge.py"]