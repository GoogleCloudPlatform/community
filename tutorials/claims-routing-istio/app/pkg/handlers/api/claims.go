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

package api

import (
	"context"
	"encoding/json"
	"log"
	"net/http"

	"example.com/claims-routing/pkg/claims"
)

const versionClaimKey = "version"

type userPrefs struct {
	Version string `json:"version"`
}

type claimsClient interface {
	GetUserID(r *http.Request) (string, error)
	GetClaim(ctx context.Context, uid, claim string) (string, error)
	AddClaim(ctx context.Context, uid, claim, value string) error
}

// UserHandler provides a Claims handlerFunc for end-user custom claims requests
type UserHandler struct {
	c claimsClient
}

// NewUserHandler creates a UserHandler
func NewUserHandler() (*UserHandler, error) {
	client, err := claims.NewClient(context.Background(), nil)
	if err != nil {
		return nil, err
	}
	return &UserHandler{
		c: client,
	}, nil
}

// Claims handles user custom claim requests
func (u *UserHandler) Claims(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		u.getClaims(w, r)
	case http.MethodPost:
		u.updateClaims(w, r)
	default:
		http.Error(w, http.StatusText(http.StatusMethodNotAllowed), http.StatusMethodNotAllowed)
	}
}

// getClaims returns user custom claims
func (u *UserHandler) getClaims(w http.ResponseWriter, r *http.Request) {
	uid, err := u.c.GetUserID(r)
	if err != nil {
		log.Printf("Error getting token from request: %+v", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	version, err := u.c.GetClaim(r.Context(), uid, versionClaimKey)
	if err != nil {
		log.Printf("Error getting user version custom claim: %+v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	userJSON, err := json.Marshal(&userPrefs{
		Version: version,
	})
	if err != nil {
		log.Printf("Error converting to JSON: %+v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	_, err = w.Write(userJSON)
	if err != nil {
		log.Printf("Could not write to response body: %+v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
}

// updateClaims updates user custom claims
func (u *UserHandler) updateClaims(w http.ResponseWriter, r *http.Request) {
	uid, err := u.c.GetUserID(r)
	if err != nil {
		log.Printf("Error getting token from request: %+v", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	var prefs userPrefs
	err = json.NewDecoder(r.Body).Decode(&prefs)
	if err != nil {
		log.Printf("Error parsing JSON: %+v", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	version := prefs.Version
	if version != "beta" {
		version = "stable" // interpret all other values as "stable"
	}
	if err := u.c.AddClaim(r.Context(), uid, versionClaimKey, version); err != nil {
		log.Printf("Error adding user version custom claim: %+v", err)
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	w.WriteHeader(http.StatusNoContent)
}
