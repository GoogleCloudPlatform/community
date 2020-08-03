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
	"testing"
)

func TestStaticPath(t *testing.T) {
	tests := []struct {
		name            string
		baseDataPathEnv string
		want            string
	}{
		{
			"default",
			"",
			"static",
		},
		{
			"env",
			"/var/run/ko",
			"/var/run/ko/static",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			os.Setenv(BaseDataPathEnv, tt.baseDataPathEnv)
			defer os.Unsetenv(BaseDataPathEnv)
			if got := StaticPath(); got != tt.want {
				t.Errorf("got = %v, want = %v", got, tt.want)
			}
		})
	}
}

func TestTemplatePath(t *testing.T) {
	tests := []struct {
		name          string
		koDataPathEnv string
		want          string
	}{
		{
			"default",
			"",
			"templates",
		},
		{
			"ko",
			"/var/run/ko",
			"/var/run/ko/templates",
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			os.Setenv(BaseDataPathEnv, tt.koDataPathEnv)
			defer os.Unsetenv(BaseDataPathEnv)
			if got := TemplatePath(); got != tt.want {
				t.Errorf("got = %v, want = %v", got, tt.want)
			}
		})
	}
}
