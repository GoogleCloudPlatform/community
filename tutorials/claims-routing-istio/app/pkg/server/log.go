// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package server

import (
	"log"
	"net/http"
	"strings"
)

func logRequest(handler http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/api") {
			log.Printf("%v %v", r.Method, r.URL.RequestURI())
		}
		handler.ServeHTTP(w, r)
	})
}

func logHeaders(handler http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasPrefix(r.URL.Path, "/api") {
			for header, values := range r.Header {
				for _, value := range values {
					if strings.ToLower(header) == "authorization" || strings.ToLower(header) == "cookie" {
						value = "[redacted]"
					}
					log.Printf("  %v: %v", header, value)
				}
			}
		}
		handler.ServeHTTP(w, r)
	})
}
