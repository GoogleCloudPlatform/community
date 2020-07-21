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

package handlers

import (
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"example.com/claims-routing/pkg/config"
)

// override template path to make it work for unit testing
var _ = os.Setenv(config.BaseDataPathEnv, "../..")

func TestIndex(t *testing.T) {
	tests := []struct {
		name       string
		r          *http.Request
		wantStatus int
	}{
		{
			name:       "returns 200 OK for requests to /",
			r:          httptest.NewRequest("GET", "/", nil),
			wantStatus: http.StatusOK,
		},
		{
			name:       "returns 404 Not Found for requests to other paths",
			r:          httptest.NewRequest("GET", "/any", nil),
			wantStatus: http.StatusNotFound,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			recorder := httptest.NewRecorder()
			Index(recorder, tt.r)
			recorder.Flush()
			gotStatus := recorder.Code
			if gotStatus != tt.wantStatus {
				t.Errorf("gotStatus = %v wantStatus = %v", gotStatus, tt.wantStatus)
			}
		})
	}
}
