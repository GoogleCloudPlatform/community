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
	"strings"

	"firebase.google.com/go/v4/auth"
)

func fakeClient() *Client {
	return &Client{
		auth: &fakeAuthClient{
			users: make(map[string]*auth.UserRecord),
		},
	}
}

// [START claims_routing_identity_platform_app_pkg_claims_client_test_fakeauthclient]
type fakeAuthClient struct {
	users map[string]*auth.UserRecord
}

var _ authClient = &fakeAuthClient{}

// VerifyIDToken fake implementation doesn't verify the JWT signature, it just
// decodes and unmarshalls the payload.
func (t *fakeAuthClient) VerifyIDToken(_ context.Context, idToken string) (*auth.Token, error) {
	jwtPayload := strings.Split(idToken, ".")[1]
	decodedPayload, err := base64.RawURLEncoding.DecodeString(jwtPayload)
	if err != nil {
		return nil, err
	}
	var token auth.Token
	err = json.Unmarshal(decodedPayload, &token)
	if err != nil {
		return nil, err
	}
	// https://github.com/firebase/firebase-admin-go/blob/v4.0.0/auth/token_verifier.go#L291
	token.UID = token.Subject
	return &token, nil
}

// GetUser fake implementation returns a auth.UserRecord that only contains the CustomClaims
// property, since this is all that's needed. The map is copied to prevent false positives and
// false negatives in unit testing.
func (t *fakeAuthClient) GetUser(_ context.Context, uid string) (*auth.UserRecord, error) {
	customClaimsCopy := map[string]interface{}{}
	for k, v := range t.users[uid].CustomClaims {
		customClaimsCopy[k] = v
	}
	return &auth.UserRecord{
		CustomClaims: customClaimsCopy,
	}, nil
}

func (t *fakeAuthClient) SetCustomUserClaims(_ context.Context, uid string, customClaims map[string]interface{}) error {
	t.users[uid].CustomClaims = customClaims
	return nil
}

// [END claims_routing_identity_platform_app_pkg_claims_client_test_fakeauthclient]
