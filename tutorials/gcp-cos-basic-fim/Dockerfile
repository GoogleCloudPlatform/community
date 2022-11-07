# Dockerfile for aide file integrity monitoring service
FROM alpine:3.8

# python3 shared with most images
RUN apk add --no-cache \
    python3 py3-pip \
  && pip3 install --upgrade pip
# Image specific layers under this line
RUN apk add --no-cache fcron rsyslog bash findutils tzdata
RUN mkdir -p /logs/archive /fim
RUN echo `date`: File created >> /logs/fimscan.log
RUN chmod +r /etc/fcron/*

COPY start.py /fim/start.py
COPY dupefinder.sh /fim/dupefinder.py
COPY scan.sh /fim/scan.sh
RUN chmod +x /fim/scan.sh

CMD /fim/start.py
