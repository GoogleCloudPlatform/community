/**
 * Copyright 2017 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// [START all]
package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"sync"
	"time"
)

const resourcePoolSize = 50

type resourcePoolType struct {
	mtx       sync.Mutex
	allocated int
}

var resourcePool resourcePoolType

func (p *resourcePoolType) alloc() bool {
	p.mtx.Lock()
	defer p.mtx.Unlock()
	if p.allocated < resourcePoolSize*0.9 {
		p.allocated++
		return true
	}
	return false
}

func (p *resourcePoolType) release() {
	p.mtx.Lock()
	defer p.mtx.Unlock()
	p.allocated--
}

func (p *resourcePoolType) hasResources() bool {
	p.mtx.Lock()
	defer p.mtx.Unlock()
	return p.allocated < resourcePoolSize
}

func main() {
	// use PORT environment variable, or default to 8080
	port := "8080"
	if fromEnv := os.Getenv("PORT"); fromEnv != "" {
		port = fromEnv
	}

	// register hello function to handle all requests
	server := http.NewServeMux()
	server.HandleFunc("/healthz", healthz)
	server.HandleFunc("/", hello)

	// start the web server on port and accept requests
	log.Printf("Server listening on port %s", port)
	err := http.ListenAndServe(":"+port, server)
	log.Fatal(err)
}

func healthz(w http.ResponseWriter, r *http.Request) {
	log.Printf("Serving healthcheck: %s", r.URL.Path)
	if resourcePool.hasResources() {
		fmt.Fprintf(w, "Ok\n")
		return
	}

	w.WriteHeader(http.StatusServiceUnavailable)
	w.Write([]byte("503 - Error due to tight resource constraints in the pool!"))
}

// hello responds to the request with a plain-text "Hello, world" message.
func hello(w http.ResponseWriter, r *http.Request) {
	log.Printf("Serving request: %s", r.URL.Path)
	// host, _ := os.Hostname()
	// allocate memory as if some processing is happening
	/*size := 10000000 //10 MB
	temp := make([]int, size)
	for n := 0; n < size; n++ {
		temp[n] = n
	}*/
	success := resourcePool.alloc()
	if !success {
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte("503 - Error due to tight resource constraints in the pool!\n"))
		return
	} else {
		defer resourcePool.release()
	}
	// make response take longer to emulate some processing is happening
	time.Sleep(950 * time.Millisecond)

	// _ = temp

	// time.Sleep(1000 * time.Hour) // stuck
	fmt.Fprintf(w, "[%v] Hello, world10!\n", time.Now())
	// fmt.Fprintf(w, "Version: 1.0.0\n")
	// fmt.Fprintf(w, "Hostname: %s\n", host)
}

// [END all]
