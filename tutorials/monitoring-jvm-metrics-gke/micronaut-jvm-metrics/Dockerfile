FROM openjdk:14-alpine
COPY build/libs/micronaut-jvm-metrics-*-all.jar micronaut-jvm-metrics.jar
EXPOSE 8080
CMD ["java", "-Dcom.sun.management.jmxremote", "-Xmx128m", "-jar", "micronaut-jvm-metrics.jar"]