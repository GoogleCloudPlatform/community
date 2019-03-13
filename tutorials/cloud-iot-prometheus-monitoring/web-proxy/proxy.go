package main

import (
	"fmt"
	"log"
	"net/http/httputil"
	"net/url"

	"net/http"
)

func main() {
	http.HandleFunc("/", proxyGrafana)
	http.HandleFunc("/_ah/health", healthCheckHandler)
	log.Print("Listening on port 8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func proxyGrafana(w http.ResponseWriter, r *http.Request) {
	// update this to the private ip address of the service
	service, _ := url.Parse("http://10.128.0.4/")
	proxy := httputil.NewSingleHostReverseProxy(service)
	proxy.ServeHTTP(w, r)
}

func healthCheckHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "ok")
}
