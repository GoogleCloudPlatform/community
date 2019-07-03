package main

import (
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"

	"github.com/caarlos0/env/v6"
	"k8s.io/client-go/transport"
)

type config struct {
	ServiceEndpoint string `env:"SERVICE_ENDPOINT"`
	TokenPath       string `env:"TOKEN_FILE" envDefault:"/var/run/secrets/tokens/gke-sa"`
}

func main() {
	cfg := config{}
	if err := env.Parse(&cfg); err != nil {
		log.Fatalf("%+v\n", err)
	}
	fmt.Printf("%v+\n", cfg)
	authTransport, err := transport.NewBearerAuthWithRefreshRoundTripper("", cfg.TokenPath, http.DefaultTransport)
	if err != nil {
		log.Fatalf("Unable to set transport: %+v\n", err)
	}

	client := &http.Client{
		Transport: authTransport,
		Timeout:   time.Second * 5,
	}

	ticker := time.NewTicker(10 * time.Second)
	quit := make(chan struct{})
	for {
		select {
		case <-ticker.C:
			go func() {
				printGet(client, cfg.ServiceEndpoint)
				printGet(client, fmt.Sprintf("%s/private", cfg.ServiceEndpoint))
			}()
		case <-quit:
			ticker.Stop()
			return
		}
	}
}

func printGet(client *http.Client, url string) {
	log.Printf("getting %s", url)
	resp, err := client.Get(url)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	fmt.Printf("%s\n", body)
}
