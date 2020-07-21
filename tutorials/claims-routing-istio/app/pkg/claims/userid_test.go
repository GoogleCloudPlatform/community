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

package claims

import (
	"encoding/base64"
	"net/http"
	"testing"
)

// sub = bar
// generated using https://github.com/istio/istio/blob/master/security/tools/jwt/samples/gen-jwt.py
const testJwt string = "eyJhbGciOiJSUzI1NiIsImtpZCI6IkRIRmJwb0lVcXJZOHQyenBBMnFYZkNtcjVWTzVaRXI0" +
	"UnpIVV8tZW52dlEiLCJ0eXAiOiJKV1QifQ.eyJleHAiOjE1ODk5NTgzNDcsImlhdCI6MTU4OTk1NDc0NywiaXNzIjoi" +
	"dGVzdGluZ0BzZWN1cmUuaXN0aW8uaW8iLCJzdWIiOiJiYXIifQ.gbYo03scik8eBrtVbKRojEYR8J15d9upwtpVL5FV" +
	"Qt1nCYGWfzsEqR9E2dPeTpCQb4hrJo1NVSWeGsWflZEFAK-z7Cyo75MM_o6GbsgUrfah_d48cNVjCbPyXb9JvYNgIsz" +
	"IuIRPXFbPkBC1Sj6a_PSym43nwAW-LjpU43bI_O7BI4-K6mwPjBfxoeddqiEbhlWqBvhbBle3fLCiw82MLnP3LqLzub" +
	"c22-0rkT9RK927I-JjctAfH0b-N5aE0EJxCW3fTbrdwXIvTzADTjKrg9Nr16LwC68hpkwbfSE6x7wjb1g6r1U_T35WQ" +
	"XW4ALQi1cGp1P8G03eJ2U3VydlReQ"

func TestClient_GetUserID_BearerToken(t *testing.T) {
	wantUID := "bar"
	c := fakeClient()
	r, err := http.NewRequest("", "", nil)
	if err != nil {
		t.Error(err)
		return
	}
	r.Header.Add("Authorization", "Bearer "+testJwt)
	uid, err := c.GetUserID(r)
	if err != nil {
		t.Errorf("error = %+v", err)
		return
	}
	if uid != wantUID {
		t.Errorf("got = %v, want = %v", uid, wantUID)
	}
}

func TestClient_GetUserID_JwtPayload(t *testing.T) {
	jwtPayload := base64.RawURLEncoding.EncodeToString([]byte(`{ "sub": "foo" }`))
	wantUID := "foo"
	c := fakeClient()
	r, err := http.NewRequest("", "", nil)
	if err != nil {
		t.Error(err)
		return
	}
	r.Header.Add("X-Jwt-Payload", jwtPayload)
	uid, err := c.GetUserID(r)
	if err != nil {
		t.Errorf("error = %+v", err)
	}
	if uid != wantUID {
		t.Errorf("got = %v, want = %v", uid, wantUID)
	}
}
