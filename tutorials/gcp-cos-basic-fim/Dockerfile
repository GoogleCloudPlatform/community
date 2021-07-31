# Dockerfile for aide file integrity monitoring service
FROM alpine:3.8
# python3 shared with most images
RUN apk add --no-cache \
    python3 py3-pip \
  && pip3 install --upgrade pip
# Image specific layers under this line
RUN apk add --no-cache fcron rsyslog bash findutils
RUN mkdir -p /logs/archive
RUN echo `date`: File created >> /logs/fimscan.log
RUN chmod +r /etc/fcron/*

COPY start.py /start.py
COPY scan.sh /scan.sh
RUN chmod +x /scan.sh

CMD /start.py
