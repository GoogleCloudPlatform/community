package main

import (
	"io/ioutil"
	"net/http"
	"strings"
	"time"

	"golang.org/x/oauth2"
)

const (
	googleRootCertURL      = "https://www.googleapis.com/oauth2/v3/certs"
	metadataIdentityDocURL = "http://metadata/computeMetadata/v1/instance/service-accounts/default/identity"
)

type idTokenSrc struct {
	aud string
}

func (ts idTokenSrc) Token() (t *oauth2.Token, err error) {
	client := &http.Client{}
	req, err := http.NewRequest("GET", metadataIdentityDocURL+"?format=full&audience="+ts.aud, nil)
	req.Header.Add("Metadata-Flavor", "Google")
	resp, err := client.Do(req)
	if err != nil {
		return &oauth2.Token{}, err
	}
	defer resp.Body.Close()

	bodyBytes, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return &oauth2.Token{}, err
	}
	t = &oauth2.Token{
		AccessToken: strings.TrimSpace(string(bodyBytes)),
		Expiry:      time.Now().Add(45 * time.Minute),
	}
	return t, nil
}

// TokenSource returns a oauth2.TokenSource that uses the current workload identity of the service
func TokenSource(aud string) oauth2.TokenSource {
	idSrc := idTokenSrc{aud: aud}
	initialToken := &oauth2.Token{}
	return oauth2.ReuseTokenSource(initialToken, idSrc)
}
