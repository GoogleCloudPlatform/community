FROM golang:1.12.5-alpine3.9 as builder
RUN apk update && apk add git && apk add ca-certificates && rm -rf /var/cache/apk/*
COPY go.* /modbuild/
WORKDIR /modbuild
RUN go mod download
COPY . /modbuild
RUN go build -o /app *.go

FROM alpine:3.9
CMD ["./app"]
EXPOSE 8080
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app .
