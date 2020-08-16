# Base image for containerized monitoring agent
ARG BASE_IMAGE_TAG=latest
FROM marketplace.gcr.io/google/debian9:${BASE_IMAGE_TAG}

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    ca-certificates

ADD https://dl.google.com/cloudagents/install-monitoring-agent.sh /install-monitoring-agent.sh

RUN bash /install-monitoring-agent.sh

RUN apt-get clean \
    && rm -rf /var/lib/apt/lists/*_*


COPY collectd.conf /etc/collectd/collectd.conf
COPY run.sh /run.sh

RUN ["chmod", "+x", "/run.sh"]

CMD /run.sh
