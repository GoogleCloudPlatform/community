package main

import (
	"context"
	"errors"
	"log"
	"net/http"
	"strings"

	"github.com/caarlos0/env/v6"
	"github.com/coreos/go-oidc"
)

// AuthConfig docs
type AuthConfig struct {
	Issuer             string `env:"ID_ISSUER"`
	Audience           string `env:"JWT_AUDIENCE"`
	AuthorizedSubjects []string
}

// AuthMiddleware docs
type AuthMiddleware struct {
	Options  AuthConfig
	verifier *oidc.IDTokenVerifier
	ctx      context.Context
}

// AuthTokenContext type for key
type AuthTokenContext struct{}

// NewAuth new middleware with options
func NewAuth(opts AuthConfig) *AuthMiddleware {
	ctx := context.Background()
	provider, err := oidc.NewProvider(ctx, opts.Issuer)
	if err != nil {
		panic(err)
	}
	return &AuthMiddleware{
		Options:  opts,
		verifier: provider.Verifier(&oidc.Config{ClientID: opts.Audience}),
		ctx:      ctx,
	}
}

// NewAuthFromEnv new middleware with options from env
func NewAuthFromEnv() *AuthMiddleware {
	opts := AuthConfig{}
	env.Parse(&opts)
	return NewAuth(opts)
}

// FromAuthHeader is a "TokenExtractor" that takes a given request and extracts
// the JWT token from the Authorization header.
func FromAuthHeader(r *http.Request) (string, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return "", errors.New("Authorization header format must be Bearer {token}")
	}

	// TODO: Make this a bit more robust, parsing-wise
	authHeaderParts := strings.Split(authHeader, " ")
	if len(authHeaderParts) != 2 || strings.ToLower(authHeaderParts[0]) != "bearer" {
		return "", errors.New("Authorization header format must be Bearer {token}")
	}

	return authHeaderParts[1], nil
}

func forbid(w http.ResponseWriter) {
	w.WriteHeader(http.StatusForbidden)
	w.Write([]byte("403 - Forbidden\n"))
	return
}

// CheckToken checks headers and validates ID Token
func (m *AuthMiddleware) CheckToken(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log.Printf("getting token for for %s", r.RequestURI)
		token, err := FromAuthHeader(r)
		if err != nil {
			// no valid auth header
			w.Header().Add("WWW-Authenticate", `Bearer realm="private API requires valid oidc-token"`)
			w.WriteHeader(http.StatusUnauthorized)
			w.Write([]byte("401 - Unauthorized\n"))
			return
		}
		// verifies issuer and audience
		idToken, err := m.verifier.Verify(m.ctx, token)
		if err != nil {
			// the token was invalid (expired, wrong issuer, wrong audience)
			log.Printf("invalid token", err)
			forbid(w)
			return
		}

		// check for authorized subjects, if none are given, all from issuer are assumed authorized
		if len(m.Options.AuthorizedSubjects) > 0 {
			authorized := false

			for _, a := range m.Options.AuthorizedSubjects {
				if a == idToken.Subject {
					authorized = true
					break
				}
			}

			if !authorized {
				forbid(w)
			}
		}
		// Update the current request with the ID Token
		newRequest := r.WithContext(context.WithValue(r.Context(), AuthTokenContext{}, idToken))
		*r = *newRequest
		// continue to handler
		next.ServeHTTP(w, r)
	}
}
