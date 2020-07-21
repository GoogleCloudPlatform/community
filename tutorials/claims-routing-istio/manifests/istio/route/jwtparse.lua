-- Copyright 2020 Google LLC
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--
-- Disclaimer: This is not an officially supported Google product.
--
-- [START claims_routing_identity_platform_istio_manifests_istio_route_jwtparse]
-- Lua Envoy filter to extract JWT claims and add them as additional request
-- headers. This filter does the following:
--
-- 1. Removes any existing X-App-Version request headers.
-- 2. Extracts the Bearer JSON Web Token (JWT) from the Authorization header.
-- 3. If there is no JWT in the Authorization header, looks for a JWT payload
--    (the second part of a JWT) in the X-Jwt-Payload header.
-- 4. base64url decodes the token payload.
-- 5. Gets the custom `version` claim from the base64url-decoded token payload.
-- 6. Adds the version claim as a header called X-App-Version to the request.
--
-- References:
-- https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/lua_filter
-- http://www.lua.org/manual/5.1/manual.html

local basexx = require("basexx")
local json = require("json")

local app_version_header = "x-app-version"
local jwt_payload_header = "x-jwt-payload"

function envoy_on_request(handle)
    handle:logDebug("JWT parse filter")
    handle:headers():remove(app_version_header)
    local authorization = handle:headers():get("authorization")
    if not authorization then
        handle:logDebug("No Authorization header in request.")
    end
    local jwt_payload_enc = handle:headers():get(jwt_payload_header)
    if authorization then
        jwt_payload_enc = string.match(authorization, "Bearer .+%.(.+)%..*")
    end
    if not jwt_payload_enc then
        handle:logWarn("No valid Bearer JWT in the Authorization header, " ..
            "and no JWT payload in the X-Jwt-Payload header.")
        return
    end
    local jwt_payload = basexx.from_url64(jwt_payload_enc)
    if not jwt_payload then
        handle:logErr("Could not base64url decode payload from Bearer JWT.")
        return
    end
    local status, version_claim = pcall(
        function() return json.decode(jwt_payload)["version"] end
    )
    if not status then
        handle:logErr("Could not parse base64url decoded JWT payload as " ..
            "valid JSON: " .. jwt_payload)
        return
    end
    if not version_claim then
        handle:logWarn("No version claim in the JWT payload.")
        return
    end
    handle:logDebug("Adding header: " ..
        app_version_header .. "=" .. version_claim)
    handle:headers():replace(app_version_header, version_claim)
end
-- [END claims_routing_identity_platform_istio_manifests_istio_route_jwtparse]
