// Copyright 2021 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
)

func main() {
	http.HandleFunc("/", home)
	port := "8080"

	if v := os.Getenv("PORT"); v != "" {
		port = v
	}
	log.Fatal(http.ListenAndServe(":"+port, nil))
}

func home(w http.ResponseWriter, req *http.Request) {
	svc := os.Getenv("REDIS_CLIENT")
	if svc == "" {
		svc = "Not set"
	}

	svcUrl := fmt.Sprintf("http://%s", svc)
	resp, err := http.Get(svcUrl)
	if err != nil {
		log.Fatalln(err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatalln(err)
	}
	//Convert the body to type string
	sb := string(body)

	log.Println(sb)
	fmt.Fprintf(w, sb)
}