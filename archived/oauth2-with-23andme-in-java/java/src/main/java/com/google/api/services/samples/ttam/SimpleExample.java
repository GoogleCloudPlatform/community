/*
 * Copyright (c) 2011 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 */

package com.google.api.services.samples.ttam;

import com.google.api.client.auth.oauth2.AuthorizationCodeFlow;
import com.google.api.client.auth.oauth2.ClientParametersAuthentication;
import com.google.api.client.auth.oauth2.Credential;
import com.google.api.client.extensions.java6.auth.oauth2.AuthorizationCodeInstalledApp;
import com.google.api.client.extensions.java6.auth.oauth2.VerificationCodeReceiver;
import com.google.api.client.extensions.jetty.auth.oauth2.LocalServerReceiver;
import com.google.api.client.http.*;
import com.google.api.client.http.javanet.NetHttpTransport;
import com.google.api.client.json.JsonFactory;
import com.google.api.client.json.JsonObjectParser;
import com.google.api.client.json.jackson2.JacksonFactory;
import com.google.api.client.util.store.DataStoreFactory;
import com.google.api.client.util.store.FileDataStoreFactory;

import java.io.File;
import java.io.IOException;
import java.util.Arrays;
import java.util.Collection;

import static com.google.api.client.auth.oauth2.BearerToken.authorizationHeaderAccessMethod;


/**
 * 23andMe API Example with Sickle Cell Anemia, using OAuth2
 *
 * Instructions:
 * 1) Create a 23andMe client at https://api.23andme.com/apply/ with a redirect_uri of http://127.0.0.1:8080/Callback
 * 2) Run this java application with two arguments: the client_id followed by the client_secret
 * 3) Authenticate, using your 23andMe credentials
 *
 * @author Dennis Byrne <dbyrne@23andme.com>
 */
public class SimpleExample {

    /**
     * The client_id field value at https://api.23andme.com/dev/
     */
    private final String clientId;
    /**
     * The client_secret field value at https://api.23andme.com/dev/
     */
    private final String clientSecret;
    private final DataStoreFactory dataStoreFactory;
    private final HttpTransport httpTransport;
    private final JsonFactory jsonFactory;

    private static final Collection<String> SCOPES = Arrays.asList("basic", "i3003137");

    private static final String DOMAIN = "127.0.0.1";
    private static final int PORT = 8080;
    private static final String BASE_URL = "https://api.23andme.com/";
    private static final String AUTHORIZATION_SERVER_URL = BASE_URL + "authorize/";
    private static final String TOKEN_SERVER_URL = BASE_URL + "token/";

    public SimpleExample(FileDataStoreFactory dataStoreFactory, String clientId, String clientSecret) {
        this.clientId = clientId;
        this.dataStoreFactory = dataStoreFactory;
        this.clientSecret = clientSecret;
        this.httpTransport = new NetHttpTransport();
        this.jsonFactory = new JacksonFactory();
    }

    public static void main(String[] args) throws Throwable {
        File directory = new File(System.getProperty("user.home"), ".store/ttam");
        if (args.length != 2) {
            throw new AssertionError("client_id and client_secret are required");
        }
        SimpleExample simpleExample = new SimpleExample(new FileDataStoreFactory(directory), args[0], args[1]);
        Genotype genotype = simpleExample.retrieveGenotype();
        System.out.println("Genotype @ i3003137, a SNP associated with Sickle Cell Anemia: " + genotype.i3003137);
    }

    public Genotype retrieveGenotype() throws Exception {
        final Credential credential = authorize();

        HttpRequestInitializer initializer = new HttpRequestInitializer() {
            public void initialize(HttpRequest request) throws IOException {
                credential.initialize(request);
                request.setParser(new JsonObjectParser(jsonFactory));
            }
        };
        HttpRequestFactory requestFactory = httpTransport.createRequestFactory(initializer);

        GenericUrl userUrl = new GenericUrl(BASE_URL + "/1/user/");
        HttpRequest userRequest = requestFactory.buildGetRequest(userUrl);
        HttpResponse userResponse = userRequest.execute();
        Account account = userResponse.parseAs(Account.class);
        Profile profile = account.profiles.get(0);

        GenericUrl genotypesUrl = new GenericUrl(BASE_URL + "1/genotypes/" + profile.id + "/?locations=i3003137");
        HttpRequest genotypesRequest = requestFactory.buildGetRequest(genotypesUrl);
        HttpResponse genotypesResponse = genotypesRequest.execute();
        return genotypesResponse.parseAs(Genotype.class);
    }

    private Credential authorize() throws Exception {
        HttpExecuteInterceptor credentials = new ClientParametersAuthentication(this.clientId, this.clientSecret);
        AuthorizationCodeFlow flow = new AuthorizationCodeFlow.Builder(authorizationHeaderAccessMethod(),
                                                             httpTransport,
                                                             jsonFactory,
                                                             new GenericUrl(TOKEN_SERVER_URL),
                                                             credentials,
                                                             this.clientId,
                                                             AUTHORIZATION_SERVER_URL)
                                                            .setScopes(SCOPES)
                                                            .setDataStoreFactory(dataStoreFactory).build();
        LocalServerReceiver.Builder builder = new LocalServerReceiver.Builder();
        VerificationCodeReceiver receiver = builder.setHost(DOMAIN)
                                                   .setPort(PORT).build();
        return new AuthorizationCodeInstalledApp(flow, receiver).authorize("user");
    }
}
