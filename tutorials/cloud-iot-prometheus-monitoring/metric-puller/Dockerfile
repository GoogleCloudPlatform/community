FROM alpine:3.4
RUN apk add --no-cache ca-certificates
ADD metric-puller /metric-puller
ENTRYPOINT ["/metric-puller"]
