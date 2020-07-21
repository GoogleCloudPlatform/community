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
	"errors"
	"log"
	"reflect"

	firebase "firebase.google.com/go/v4"
	"firebase.google.com/go/v4/auth"
	"google.golang.org/api/option"
)

// Client contains a Identity Platform / Firebase Auth client. Use this for
// validating ID tokens and getting and updating user custom claims.
// Client is safe for use by multiple concurrent goroutines
type Client struct {
	auth authClient
}

// [START claims_routing_identity_platform_app_pkg_claims_client_authclient]
// authClient constrains the surface area of auth.Client to assist in unit testing.
type authClient interface {
	VerifyIDToken(ctx context.Context, idToken string) (*auth.Token, error)
	GetUser(ctx context.Context, uid string) (*auth.UserRecord, error)
	SetCustomUserClaims(ctx context.Context, uid string, customClaims map[string]interface{}) error
}

// [END claims_routing_identity_platform_app_pkg_claims_client_authclient]

// NewClient creates a new Client
func NewClient(ctx context.Context, config *firebase.Config, opts ...option.ClientOption) (*Client, error) {
	app, err := firebase.NewApp(ctx, config, opts...)
	if err != nil {
		return nil, err
	}
	projectID := reflect.ValueOf(*app).FieldByName("projectID").String()
	if projectID == "" {
		return nil, errors.New("missing projectID, this means the app could not find credentials")
	}
	log.Printf("projectID=%v\n", projectID)
	auth, err := app.Auth(ctx)
	if err != nil {
		return nil, err
	}
	return &Client{
		auth: auth,
	}, nil
}
