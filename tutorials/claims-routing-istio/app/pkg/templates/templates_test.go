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

package templates

import (
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"

	"example.com/claims-routing/pkg/config"
)

// override template path to make it work for unit testing
var _ = os.Setenv(config.BaseDataPathEnv, "../..")

func TestExecuteTemplate(t *testing.T) {
	recorder := httptest.NewRecorder()
	Execute(recorder, "index", nil)
	recorder.Flush()
	wantStatus := http.StatusOK
	gotStatus := recorder.Code
	if gotStatus != wantStatus {
		t.Errorf("gotStatus = %v wantStatus = %v", gotStatus, wantStatus)
	}
	wantBody := `<!doctype html>`
	b := make([]byte, len(wantBody)+1) // cater for potential extra newline
	recorder.Body.Read(b)
	gotBody := strings.TrimSpace(string(b))
	if gotBody != wantBody {
		t.Errorf("gotBody = %v wantBody = %v", gotBody, wantBody)
	}
}

func TestExecuteTemplate_missing(t *testing.T) {
	recorder := httptest.NewRecorder()
	Execute(recorder, "missing", nil)
	recorder.Flush()
	want := http.StatusInternalServerError
	got := recorder.Code
	if got != want {
		t.Errorf("got = %v want = %v", got, want)
	}
}
