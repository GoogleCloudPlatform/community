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

local lu = require("luaunit")
require("jwtparse")

-- set debug to true to see print output during tests
local debug = os.getenv("DEBUG") == "true" or false
local app_version_header = "x-app-version"
local jwt_payload_header = "x-jwt-payload"

local function fakeRequestHandle(authorization, jwtPayload, appVersion)
    local _headers = {}
    _headers["authorization"] = authorization
    _headers[jwt_payload_header] = jwtPayload
    _headers[app_version_header] = appVersion
    return {
        headers = function(_)
            return {
                get = function (_, headerName)
                    return _headers[string.lower(headerName)]
                end,
                remove = function (_, headerName)
                    _headers[string.lower(headerName)] = nil
                end,
                replace = function (_, headerName, headerValue)
                    _headers[string.lower(headerName)] = headerValue
                end,
            }
        end,
        logTrace = function (_, msg)
            if debug then
                print("TRACE: " .. msg)
            end
        end,
        logDebug = function (_, msg)
            if debug then
                print("DEBUG: " .. msg)
            end
        end,
        logInfo = function (_, msg)
            if debug then
                print("INFO: " .. msg)
            end
        end,
        logWarn = function (_, msg)
            if debug then
                print("WARN: " .. msg)
            end
        end,
        logErr = function (_, msg)
            if debug then
                print("ERROR: " .. msg)
            end
        end,
    }
end

local TestJwtParse = {}

local token_with_version_claim_beta = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkRIRmJw" ..
"b0lVcXJZOHQyenBBMnFYZkNtcjVWTzVaRXI0UnpIVV8tZW52dlEiLCJ0eXAiOiJKV1QifQ.eyJ" ..
"leHAiOjE1ODk4NjQ3MjIsImlhdCI6MTU4OTg2MTEyMiwiaXNzIjoidGVzdGluZ0BzZWN1cmUua" ..
"XN0aW8uaW8iLCJzdWIiOiJ0ZXN0aW5nQHNlY3VyZS5pc3Rpby5pbyIsInZlcnNpb24iOiJiZXR" ..
"hIn0.I6E7pV9JWBOQTWnAku22-cbZlIwulqkMRXFhPGM7UTgwYkFkKItkHU0E6rUapsgFQiuLh" ..
"Ys2emA6nckAlPWXvaRtMpTfQp7lrt0ftuFNYKulZg1RYffI8c_J2eTkm_-riwWIv_vpJRICz3n" ..
"omCGYG1A5Tw7FW1Cu2eFnL12X6_kn-f6RJ_Qhw2nqH2gvVcJZXCky8jnP09mKO3ljvn3EQCc-0" ..
"h4quhhNskFVVFHZsmb9fzm4PcY5f_c4Do0xzaAa8K0dY-Wz3Kozdv7xB1pamPEysqkNQG2iePf" ..
"LEW35YZI0oVQ0WkuLKfsfHG1O38vrVYoYfmVeRae8muYUXnADlw"

local token_payload_with_version_claim_beta = "eyJleHAiOjE1ODk4NjQ3MjIsImlh" ..
"dCI6MTU4OTg2MTEyMiwiaXNzIjoidGVzdGluZ0BzZWN1cmUuaXN0aW8uaW8iLCJzdWIiOiJ0ZX" ..
"N0aW5nQHNlY3VyZS5pc3Rpby5pbyIsInZlcnNpb24iOiJiZXRhIn0"

local token_without_version_claim = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkRIRmJwb0" ..
"lVcXJZOHQyenBBMnFYZkNtcjVWTzVaRXI0UnpIVV8tZW52dlEiLCJ0eXAiOiJKV1QifQ.eyJle" ..
"HAiOjE1ODk4NjQ3MzksImlhdCI6MTU4OTg2MTEzOSwiaXNzIjoidGVzdGluZ0BzZWN1cmUuaXN" ..
"0aW8uaW8iLCJzdWIiOiJ0ZXN0aW5nQHNlY3VyZS5pc3Rpby5pbyJ9.AcsSZguf7ovRypi3Yv2w" ..
"0e-V1_fJj-ZL3bVnfj2YqUSltI0zXjbMaZqXnBdbTUAM-m6f1rZ3DBkziDexYaO-1uDdJdF8fP" ..
"svuRtRFNlpvu5gBUuMMjSy0YyPrFl43eL3YDoMHlTUjhapb11cfqZqdU6Dh4ZrtESPNnkF5y32" ..
"Zkt1UpWnsgR6-8OsregJDYrBg1QtyfujbJ0Vm1V7WyzJfK-c6wUjuFV6Ubw1Han2jZFw1Dd0Iu" ..
"nJku62QoA9bIie9dHKUk-RMPxysJcPZp983Gp0fQMmV9s0qcoIh1vvqnBu4xQ0PVXeZGd0IVlY" ..
"NmPDeIT7mM62XKMPq2zXP0Yz3A"

function TestJwtParse.test_shouldRemoveExistingAppVersionHeader()
    local handle = fakeRequestHandle(nil, nil, "remove-me")
    envoy_on_request(handle)
    lu.assertNil(handle:headers():get(app_version_header))
end

function TestJwtParse.test_shouldSetAppVersionHeaderFromBearerToken()
    local handle = fakeRequestHandle("Bearer " .. token_with_version_claim_beta, nil, nil)
    envoy_on_request(handle)
    lu.assertEquals(handle:headers():get(app_version_header), "beta")
end

function TestJwtParse.test_shouldSetAppVersionHeaderFromTokenPayload()
    local handle = fakeRequestHandle(nil, token_payload_with_version_claim_beta, nil)
    envoy_on_request(handle)
    lu.assertEquals(handle:headers():get(app_version_header), "beta")
end

function TestJwtParse.test_shouldIgnoreMissingAuthorizationAndJwtPayloadHeaders()
    local handle = fakeRequestHandle(nil, nil, nil)
    envoy_on_request(handle)
    lu.assertNil(handle:headers():get(app_version_header))
end

function TestJwtParse.test_shouldIgnoreMissingBearerTokenInAuthorizationHeader()
    local handle = fakeRequestHandle("Bearer", nil, nil)
    envoy_on_request(handle)
    lu.assertNil(handle:headers():get(app_version_header))
end

function TestJwtParse.test_shouldIgnoreMissingCustomVersionClaimInBearerToken()
    local handle = fakeRequestHandle("Bearer " .. token_without_version_claim, nil, nil)
    envoy_on_request(handle)
    lu.assertNil(handle:headers():get(app_version_header))
end

function TestJwtParse.test_shouldIgnoreMalformedToken()
    local handle = fakeRequestHandle("Bearer foo", nil, nil)
    envoy_on_request(handle)
    lu.assertNil(handle:headers():get(app_version_header))
end

function TestJwtParse.test_shouldIgnoreMalformedTokenPayload()
    local handle = fakeRequestHandle(nil, "bar", nil)
    envoy_on_request(handle)
    lu.assertNil(handle:headers():get(app_version_header))
end

function TestJwtParse.test_shouldIgnoreMalformedTokenWithDotsLikeJwt()
    local handle = fakeRequestHandle("Bearer b.a.z", nil, nil)
    envoy_on_request(handle)
    lu.assertNil(handle:headers():get(app_version_header))
end

local luaunit = lu.LuaUnit.new()
luaunit:setOutputType("tap")
os.exit(luaunit:runSuiteByInstances({{"jwtparse", TestJwtParse }}))
