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

	"example.com/claims-routing/pkg/config"
	"example.com/claims-routing/pkg/handlers"
	"example.com/claims-routing/pkg/handlers/api"
)

// Start a HTTP server on the provided network address
// [START claims_routing_identity_platform_istio_app_pkg_server_server_go]
func Start(addr string) error {
	// authenticated URL paths
	userHandler, err := api.NewUserHandler()
	if err != nil {
		return err
	}
	http.HandleFunc("/api/user", userHandler.Claims)
	if config.Is("BETA") {
		http.HandleFunc("/api/beta", api.Beta)
	}

	// public URL paths
	http.Handle("/static/", http.StripPrefix("/static/",
		http.FileServer(http.Dir(config.StaticPath()))))
	http.HandleFunc("/prefs", handlers.Prefs)
	http.HandleFunc("/signin", handlers.SignIn)
	http.HandleFunc("/healthz", handlers.Health)
	if config.Is("BETA") {
		http.HandleFunc("/beta", handlers.Beta)
	}
	http.HandleFunc("/", handlers.Index)

	var handler http.Handler = http.DefaultServeMux
	if config.Is("DEBUG") {
		handler = logHeaders(handler)
	}
	handler = logRequest(handler)
	log.Printf("Listening on %s", addr)
	return http.ListenAndServe(addr, handler)
}

// [END claims_routing_identity_platform_istio_app_pkg_server_server_go]
