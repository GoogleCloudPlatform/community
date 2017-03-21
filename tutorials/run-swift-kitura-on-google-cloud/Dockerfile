FROM ibmcom/swift-ubuntu:latest
LABEL Description="Docker image for Swift + Kitura on GAE Flex."

# Expose default port for GAE
EXPOSE 8080

# Copy sources
RUN mkdir /root/KituraGAE
ADD main.swift /root/KituraGAE
ADD Package.swift /root/KituraGAE

# Build the app
RUN cd /root/KituraGAE && swift build

# Run the app
USER root
CMD ["/root/KituraGAE/.build/debug/KituraGAE"]
