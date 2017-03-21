FROM ibmcom/swift-ubuntu:latest
LABEL Description="Docker image for Swift + Perfect on GAE Flex."

# Get extra dependencies for Perfect
RUN apt-get update && apt-get install -y \
    openssl \
    libssl-dev \
    uuid-dev

# Expose default port for GAE
EXPOSE 8080

# Copy sources
RUN mkdir /root/PerfectGAE
ADD main.swift /root/PerfectGAE
ADD Package.swift /root/PerfectGAE

# Build the app
RUN cd /root/PerfectGAE && swift build

# Run the app
USER root
CMD ["/root/PerfectGAE/.build/debug/PerfectGAE"]
