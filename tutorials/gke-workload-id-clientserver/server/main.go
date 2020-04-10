package main

import (
	"fmt"
	"log"
	"net/http"
)

func main() {
	auth := NewAuthFromEnv()
	// Add a line like this if you want to enforce specific subject membership
	// auth.Options.AuthorizedSubjects = []string{"bob"}
	http.HandleFunc("/", exposedAPI)
	http.Handle("/private", auth.CheckToken(guardedAPI))
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}

func guardedAPI(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, `{"msg": "hello-guarded"}`)
}

func exposedAPI(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, `{"msg": "hello-exposed"}`)
}
