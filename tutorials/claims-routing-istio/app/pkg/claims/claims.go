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
	"fmt"
)

// GetClaim returns the string value of the custom claim for the user specified
// by the uid parameter, or an empty string if the user doesn't have the
// custom claim.
// [START claims_routing_identity_platform_app_pkg_claims_claims_getclaim]
func (c *Client) GetClaim(ctx context.Context, uid, claim string) (string, error) {
	user, err := c.auth.GetUser(ctx, uid)
	if err != nil {
		return "", err
	}
	value, exists := user.CustomClaims[claim]
	if !exists {
		return "", nil
	}
	return fmt.Sprintf("%v", value), nil
}

// [END claims_routing_identity_platform_app_pkg_claims_claims_getclaim]

// AddClaim adds the provided claim to the user specified by the uid parameter.
// If the user already has the claim, the value is replaced with the provided
// value argument. All other existing custom claims are retained.
// Concurrent updates of multiple claims for the same user are not safe.
func (c *Client) AddClaim(ctx context.Context, uid, claim, value string) error {
	user, err := c.auth.GetUser(ctx, uid)
	if err != nil {
		return err
	}
	customClaims := user.CustomClaims
	if customClaims == nil || len(customClaims) == 0 {
		customClaims = map[string]interface{}{}
	}
	customClaims[claim] = value
	err = c.auth.SetCustomUserClaims(ctx, uid, customClaims)
	if err != nil {
		return err
	}
	return nil
}
