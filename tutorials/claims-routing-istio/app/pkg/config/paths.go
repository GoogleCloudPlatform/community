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

package config

import (
	"os"
	"path"
)

// BaseDataPathEnv is the name of the optional environment variable that
// specifies the base directory for static files and HTML templates.
// If this environment variable is not provided, or if the value is an empty
// string, then "." is the fallback value.
const BaseDataPathEnv = "KO_DATA_PATH"

// dataPath returns the base path to files accompanying the executable.
func dataPath() string {
	path := "."
	if baseDataPath, exists := os.LookupEnv(BaseDataPathEnv); exists {
		path = baseDataPath
	}
	return path
}

// StaticPath returns the path to the static files.
func StaticPath() string {
	return path.Join(dataPath(), "static")
}

// TemplatePath returns the path to the template files.
func TemplatePath() string {
	return path.Join(dataPath(), "templates")
}
