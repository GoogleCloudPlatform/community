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
	"testing"

	"firebase.google.com/go/v4/auth"
)

func TestClient_GetClaim_ReturnsEmptyStringForMissingClaim(t *testing.T) {
	uid := "foo"
	c := &Client{
		auth: &fakeAuthClient{
			users: map[string]*auth.UserRecord{
				uid: {},
			},
		},
	}
	claim, err := c.GetClaim(context.Background(), "foo", "version")
	if err != nil {
		t.Error(err)
		return
	}
	wantClaim := ""
	if claim != wantClaim {
		t.Errorf("got = %v, want = %v", claim, wantClaim)
	}
}

// [START claims_routing_identity_platform_app_pkg_claims_claims_test_getclaim]
func TestClient_GetClaim(t *testing.T) {
	uid := "foo"
	c := &Client{
		auth: &fakeAuthClient{
			users: map[string]*auth.UserRecord{
				uid: {
					CustomClaims: map[string]interface{}{
						"version": "beta",
					},
				},
			},
		},
	}
	claim, err := c.GetClaim(context.Background(), uid, "version")
	if err != nil {
		t.Error(err)
		return
	}
	wantClaim := "beta"
	if claim != wantClaim {
		t.Errorf("got = %v, want = %v", claim, wantClaim)
	}
}

// [END claims_routing_identity_platform_app_pkg_claims_claims_test_getclaim]

func TestClient_AddClaim(t *testing.T) {
	uid := "bar"
	c := &Client{
		auth: &fakeAuthClient{
			users: map[string]*auth.UserRecord{
				uid: {},
			},
		},
	}
	ctx := context.Background()
	err := c.AddClaim(ctx, uid, "version", "alpha")
	if err != nil {
		t.Error(err)
		return
	}
	claim, err := c.GetClaim(ctx, uid, "version")
	if err != nil {
		t.Error(err)
		return
	}
	wantClaim := "alpha"
	if claim != wantClaim {
		t.Errorf("got = %v, want = %v", claim, wantClaim)
	}
}

func TestClient_AddClaim_ReplacesExistingClaim(t *testing.T) {
}
