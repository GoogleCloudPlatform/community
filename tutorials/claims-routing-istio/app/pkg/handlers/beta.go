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

	"example.com/claims-routing/pkg/config"
	"example.com/claims-routing/pkg/templates"
)

// Beta returns the beta version of the main app page
func Beta(w http.ResponseWriter, r *http.Request) {
	data := config.TemplateData()
	data["beta"] = true
	templates.Execute(w, "beta", data)
}
