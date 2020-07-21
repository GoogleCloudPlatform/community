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

package claims

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
)

// Token contains fields from the ID token used in this app
type Token struct {
	UID string
}

// GetUserID returns the user ID from the request token or token payload.
// This function first looks for a Bearer token (JWT) in the Authorization header.
// If there is no Bearer token, it looks for a JWT payload (the second part of
// the JWT, without the header or signature) in the X-Jwt-Payload header.
func (c *Client) GetUserID(r *http.Request) (string, error) {
	if strings.HasPrefix(r.Header.Get("Authorization"), "Bearer ") {
		return c.getUserIDFromBearerToken(r.Header.Get("Authorization"))
	}
	if len(r.Header.Get("X-Jwt-Payload")) == 0 {
		return "", errors.New("no Bearer token or token payload in request")
	}
	return getUserIDFromJwtPayload(r.Header.Get("X-Jwt-Payload"))
}

func (c *Client) getUserIDFromBearerToken(authHeader string) (string, error) {
	authHeaderSplit := strings.Split(authHeader, "Bearer ")
	if len(authHeaderSplit) < 2 || authHeaderSplit[1] == "" {
		return "", errors.New("Could not get token from Authorization header: " + authHeader)
	}
	idToken := authHeaderSplit[1]
	firebaseIDToken, err := c.auth.VerifyIDToken(context.Background(), idToken)
	if err != nil {
		return "", err
	}
	return firebaseIDToken.UID, nil
}

func getUserIDFromJwtPayload(jwtPayload string) (string, error) {
	decodedBytes, err := base64.RawURLEncoding.DecodeString(jwtPayload)
	if err != nil {
		return "", err
	}
	var claims map[string]interface{}
	err = json.Unmarshal(decodedBytes, &claims)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("%v", claims["sub"]), nil
}
