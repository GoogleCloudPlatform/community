FROM ibmcom/swift-ubuntu:latest
LABEL Description="Docker image for Swift + Vapor on GAE Flex."

# Expose default port for GAE
EXPOSE 8080

# Copy sources
RUN mkdir /root/VaporGAE
ADD main.swift /root/VaporGAE
ADD Package.swift /root/VaporGAE

# Build the app
RUN cd /root/VaporGAE && swift build

# Run the app
USER root
CMD ["/root/VaporGAE/.build/debug/VaporGAE"]
