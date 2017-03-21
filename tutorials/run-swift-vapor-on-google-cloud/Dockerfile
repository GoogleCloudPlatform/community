FROM ibmcom/swift-ubuntu:latest
LABEL Description="Docker image for Swift + Vapor on GAE."

# Expose default port for GAE
EXPOSE 8080

# Add app source
ADD . /app
WORKDIR /app

# Build release
RUN swift build --configuration release

# Run the app
ENTRYPOINT [".build/release/VaporGAE"]
