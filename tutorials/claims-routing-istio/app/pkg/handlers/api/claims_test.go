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
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

type fakeClaimsClient struct {
	userIDToVersion map[string]string
}

func (f *fakeClaimsClient) GetUserID(r *http.Request) (string, error) {
	return r.RequestURI, nil
}

func (f *fakeClaimsClient) GetClaim(ctx context.Context, uid, claim string) (string, error) {
	return f.userIDToVersion[uid], nil
}

func (f *fakeClaimsClient) AddClaim(ctx context.Context, uid, claim, value string) error {
	if claim != versionClaimKey {
		return fmt.Errorf("unexpected claim key: %v", claim)
	}
	f.userIDToVersion[uid] = value
	return nil
}

func TestClaims_ClaimsHandlerReturnsVersionClaimForGetRequest(t *testing.T) {
	u := &UserHandler{
		c: &fakeClaimsClient{
			userIDToVersion: map[string]string{
				"/userID": "beta",
			},
		},
	}
	recorder := httptest.NewRecorder()
	u.Claims(recorder, httptest.NewRequest("GET", "/userID", nil))
	recorder.Flush()
	wantStatus := http.StatusOK
	gotStatus := recorder.Code
	if gotStatus != wantStatus {
		t.Errorf("gotStatus = %v wantStatus = %v", gotStatus, wantStatus)
	}
	var prefs userPrefs
	_ = json.NewDecoder(bytes.NewReader(recorder.Body.Bytes())).Decode(&prefs)
	got := prefs.Version
	want := "beta"
	if got != want {
		t.Errorf("got = %v want = %v", got, want)
	}
}

func TestClaims_ClaimsHandlerUpdatesVersionClaimForPostRequest(t *testing.T) {
	userIDToVersion := map[string]string{
		"/user": "stable",
	}
	u := &UserHandler{
		c: &fakeClaimsClient{
			userIDToVersion: userIDToVersion,
		},
	}
	recorder := httptest.NewRecorder()
	userJSON, _ := json.Marshal(&userPrefs{
		Version: "beta",
	})
	u.Claims(recorder, httptest.NewRequest("POST", "/user", bytes.NewReader(userJSON)))
	recorder.Flush()
	wantStatus := http.StatusNoContent
	gotStatus := recorder.Code
	if gotStatus != wantStatus {
		t.Errorf("gotStatus = %v wantStatus = %v", gotStatus, wantStatus)
	}
	got := userIDToVersion["/user"]
	want := "beta"
	if got != want {
		t.Errorf("got = %v want = %v", got, want)
	}
}

func TestClaims_ClaimsHandlerUpdatesVersionClaimToStableForInvalidClaimValue(t *testing.T) {
	userIDToVersion := map[string]string{
		"/user": "beta",
	}
	u := &UserHandler{
		c: &fakeClaimsClient{
			userIDToVersion: userIDToVersion,
		},
	}
	recorder := httptest.NewRecorder()
	userJSON, _ := json.Marshal(&userPrefs{
		Version: "invalid",
	})
	u.Claims(recorder, httptest.NewRequest("POST", "/user", bytes.NewReader(userJSON)))
	recorder.Flush()
	wantStatus := http.StatusNoContent
	gotStatus := recorder.Code
	if gotStatus != wantStatus {
		t.Errorf("gotStatus = %v wantStatus = %v", gotStatus, wantStatus)
	}
	got := userIDToVersion["/user"]
	want := "stable"
	if got != want {
		t.Errorf("got = %v want = %v", got, want)
	}
}
