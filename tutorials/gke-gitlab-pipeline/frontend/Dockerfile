FROM openjdk:8-jdk-alpine
VOLUME /tmp
COPY target/frontend-0.0.1-SNAPSHOT.jar app.jar
ENV JAVA_OPTS=""
ENTRYPOINT exec java -Dserver.port=8081 -jar /app.jar
