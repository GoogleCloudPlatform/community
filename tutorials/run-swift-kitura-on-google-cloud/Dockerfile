FROM ibmcom/swift-ubuntu:latest
LABEL Description="Docker image for Swift + Kitura on Google App Engine flexible environment."

# Expose default port for App Engine
EXPOSE 8080

# Add app source
ADD . /app
WORKDIR /app

# Build release
RUN swift build --configuration release

# Run the app
ENTRYPOINT [".build/release/KituraGAE"]
