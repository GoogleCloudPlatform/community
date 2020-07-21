#!/usr/bin/env bash
#
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -euf -o pipefail

DEPS_DIR=$(dirname "$0")

if [ ! -f "$DEPS_DIR/basexx.lua" ]; then
    curl -sSL https://raw.githubusercontent.com/aiq/basexx/v0.4.1/LICENSE | sed 's/^/-- /' > "$DEPS_DIR/basexx.lua"
    curl -sSL https://raw.githubusercontent.com/aiq/basexx/v0.4.1/lib/basexx.lua >> "$DEPS_DIR/basexx.lua"
fi

if [ ! -f "$DEPS_DIR/json.lua" ]; then
    curl -sSLo "$DEPS_DIR/json.lua" https://raw.githubusercontent.com/rxi/json.lua/v0.1.2/json.lua
fi

if [ ! -f "$DEPS_DIR/luaunit.lua" ]; then
    curl -sSLo "$DEPS_DIR/luaunit.lua" https://raw.githubusercontent.com/bluebird75/luaunit/LUAUNIT_V3_3/luaunit.lua
fi
