package main

import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	auth := NewAuthFromEnv()
	// auth.Options.AuthorizedSubjects = []string{"bob"}
	http.HandleFunc("/", publicAPI)
	http.Handle("/private", auth.CheckToken(privateAPI))
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}

func privateAPI(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, `{"msg": "hello-private"}`)
}

func publicAPI(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, `{"msg": "hello-public"}`)
}
