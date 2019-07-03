FROM golang:1.13-alpine3.10 as builder
RUN apk update && apk add git && apk add ca-certificates && rm -rf /var/cache/apk/*
COPY go.* /modbuild/
WORKDIR /modbuild
ENV GOPROXY=https://proxy.golang.org
RUN go mod download
COPY . /modbuild
RUN go build -o /app *.go

FROM alpine:3.10
CMD ["./app"]
EXPOSE 8080
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app .
