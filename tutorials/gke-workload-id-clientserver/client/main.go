package main

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"time"

	"golang.org/x/oauth2"

	"github.com/caarlos0/env/v6"
	"k8s.io/client-go/transport"
)

type config struct {
	ServiceEndpoint string `env:"SERVICE_ENDPOINT"`
	TokenPath       string `env:"TOKEN_FILE" envDefault:"/var/run/secrets/tokens/gke-sa"`
	IdentityType    string `env:"IDENTITY" envDefault:"cluster"`
}

func main() {
	cfg := config{}
	if err := env.Parse(&cfg); err != nil {
		log.Fatalf("%+v\n", err)
	}
	fmt.Printf("%v+\n", cfg)
	var client *http.Client
	var logHeader string
	switch cfg.IdentityType {
	case "cluster":
		// This uses the projected service account with cluster OIDC identity
		authTransport, err := transport.NewBearerAuthWithRefreshRoundTripper("", cfg.TokenPath, http.DefaultTransport)
		if err != nil {
			log.Fatalf("Unable to set transport: %+v\n", err)
		}

		client = &http.Client{
			Transport: authTransport,
			Timeout:   time.Second * 5,
		}
		logHeader = "##### Projected token client"
	case "google":
		ts := TokenSource(cfg.ServiceEndpoint)
		client = oauth2.NewClient(context.TODO(), ts)
		logHeader = "##### mapped GCP SvcAccnt via Metadata server"
	}

	ticker := time.NewTicker(10 * time.Second)
	quit := make(chan struct{})
	for {
		select {
		case <-ticker.C:
			go func() {
				fmt.Println(logHeader)
				printGet(client, cfg.ServiceEndpoint)
				printGet(client, fmt.Sprintf("%s/private", cfg.ServiceEndpoint))
				fmt.Println()
			}()
		case <-quit:
			ticker.Stop()
			return
		}
	}
}

func printGet(client *http.Client, url string) {
	resp, err := client.Get(url)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	log.Printf("resp from %s:\n%s\n", url, body)
}
