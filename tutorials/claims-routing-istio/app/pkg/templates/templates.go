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
	"html/template"
	"log"
	"net/http"
	"path"
	"sync"

	"example.com/claims-routing/pkg/config"
)

var (
	doOnce    sync.Once
	templates *template.Template
)

// Execute applies the provided data objects to the template with the given
// name and writes the output to the provided ResponseWriter. In case of an
// error, it logs the error and outputs minimal error information to the
// ResponseWriter.
func Execute(w http.ResponseWriter, name string, data interface{}) {
	doOnce.Do(func() {
		templates = template.Must(template.ParseGlob(path.Join(config.TemplatePath(), "*.gohtml")))
	})
	if err := templates.ExecuteTemplate(w, name+".gohtml", data); err != nil {
		log.Printf("Error executing template %v: %+v", name, err)
		http.Error(w, http.StatusText(http.StatusInternalServerError), http.StatusInternalServerError)
	}
}
