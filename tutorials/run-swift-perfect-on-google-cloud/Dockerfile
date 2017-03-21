FROM ibmcom/swift-ubuntu:latest
LABEL Description="Docker image for Swift + Perfect on Google App Engine flexible environment."

# Get extra dependencies for Perfect
RUN apt-get update && apt-get install -y \
    openssl \
    libssl-dev \
    uuid-dev

# Expose default port for App Engine
EXPOSE 8080

# Add app source
ADD . /app
WORKDIR /app

# Build release
RUN swift build --configuration release

# Run the app
ENTRYPOINT [".build/release/PerfectGAE"]
