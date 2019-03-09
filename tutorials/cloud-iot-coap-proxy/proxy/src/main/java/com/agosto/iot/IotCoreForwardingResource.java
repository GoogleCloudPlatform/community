package com.agosto.iot;

import com.google.gson.Gson;
import org.apache.http.*;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.utils.URLEncodedUtils;
import org.apache.http.concurrent.FutureCallback;
import org.apache.http.entity.ByteArrayEntity;
import org.apache.http.impl.nio.client.CloseableHttpAsyncClient;
import org.apache.http.protocol.BasicHttpContext;
import org.eclipse.californium.compat.CompletableFuture;
import org.eclipse.californium.core.coap.CoAP.ResponseCode;
import org.eclipse.californium.core.coap.Request;
import org.eclipse.californium.core.coap.Response;
import org.eclipse.californium.proxy.*;
import org.eclipse.californium.proxy.resources.ForwardingResource;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URLDecoder;
import java.util.Arrays;
import java.util.Base64;
import java.util.Map;
import java.util.HashMap;
import java.util.List;
import java.util.stream.Collectors;
import java.util.zip.GZIPInputStream;


public class IotCoreForwardingResource extends ForwardingResource {

    private static final Logger LOGGER = LoggerFactory.getLogger(IotCoreForwardingResource.class);

    private static final int KEEP_ALIVE = 5000;
    // TODO: Properties.std.getInt("HTTP_CLIENT_KEEP_ALIVE");

    /**
     * DefaultHttpClient is thread safe. It is recommended that the same
     * instance of this class is reused for multiple request executions.
     */
    private static final CloseableHttpAsyncClient asyncClient = HttpClientFactory.createClient();
    private static final Gson gson = new Gson();


    public IotCoreForwardingResource() {
        // set the resource hidden
//		this("proxy/httpClient");
        this("iotCoreProxy");
    }

    public IotCoreForwardingResource(String name) {
        // set the resource hidden
        super(name, true);
        getAttributes().setTitle("Forward the requests to Iot Core.");
    }

    @Override
    public CompletableFuture<Response> forwardRequest(Request request) {
        final CompletableFuture<Response> future = new CompletableFuture<>();
        final Request incomingCoapRequest = request;

        // check the invariant: the request must have the proxy-uri set
        if (!incomingCoapRequest.getOptions().hasProxyUri()) {
            LOGGER.warn("Proxy-uri option not set.");
            future.complete(new Response(ResponseCode.BAD_OPTION));
            return future;
        }

        // remove the fake uri-path // TODO: why? still necessary in new Cf?
        incomingCoapRequest.getOptions().clearUriPath(); // HACK

        // get the proxy-uri set in the incoming coap request
        URI proxyUri;
        try {
            String proxyUriString = URLDecoder.decode(
                    incomingCoapRequest.getOptions().getProxyUri(), "UTF-8");
            proxyUri = new URI(proxyUriString);
        } catch (UnsupportedEncodingException e) {
            LOGGER.warn("Proxy-uri option malformed: {}", e.getMessage());
            future.complete(new Response(CoapTranslator.STATUS_FIELD_MALFORMED));
            return future;
        } catch (URISyntaxException e) {
            LOGGER.warn("Proxy-uri option malformed: {}", e.getMessage());
            future.complete(new Response(CoapTranslator.STATUS_FIELD_MALFORMED));
            return future;
        }

        //LOGGER.info(proxyUri.getPath());
        //LOGGER.info(proxyUri.getQuery());

        List<NameValuePair> params = URLEncodedUtils.parse(proxyUri, "UTF-8");
        //LOGGER.info(params.toString());

        String jwt_token = null;
        for (NameValuePair param : params) {
            //LOGGER.info(param.getName() + " : " + param.getValue());
            if ("jwt".equalsIgnoreCase(param.getName())) {
                jwt_token = param.getValue();
                break;
            }
        }

        if (jwt_token == null) {
            LOGGER.warn("jwt token was not supplied as query parameter");
            future.complete(new Response(CoapTranslator.STATUS_FIELD_MALFORMED));
            return future;
        }

        //LOGGER.info(jwt_token);

        /*
        GET https://cloudiotdevice.googleapis.com/v1/{name=projects/???/locations/???/registries/???/devices/???}/config
        POST https://cloudiotdevice.googleapis.com/v1/{name=projects/???/locations/???/registries/???/devices/???}:publishEvent
        POST https://cloudiotdevice.googleapis.com/v1/{name=projects/???/locations/???/registries/???/devices/???}:setState
         */
        List<String> paths = Arrays.asList(proxyUri.getPath().split("/"));
        if (paths.size() != 5) {
            LOGGER.warn("proxy-uri path should have five parts; only " + paths.size() + " found.");
            future.complete(new Response(CoapTranslator.STATUS_FIELD_MALFORMED));
            return future;
        }
        String project = paths.get(0);
        String location = paths.get(1);
        String registry = paths.get(2);
        String device = paths.get(3);
        String action = paths.get(4);

        //LOGGER.info(paths.toString());

        HttpRequest httpRequest;

        String iotCoreName = String.format("/v1/projects/%s/locations/%s/registries/%s/devices/%s", project, location, registry, device);

        String contentJson;

        if ("config".equalsIgnoreCase(action)) {
            iotCoreName += "/" + action;
            httpRequest = new HttpGet(iotCoreName);
        } else {
            iotCoreName += ":" + action;
            httpRequest = new HttpPost(iotCoreName);
            httpRequest.setHeader("content-type", "application/json");

            HashMap content = new HashMap();
            String payloadEncoded = Base64.getEncoder().encodeToString(incomingCoapRequest.getPayload());
            content.put("binaryData", payloadEncoded);
            if ("setState".equalsIgnoreCase(action)) {
                HashMap state = new HashMap();
                state.put("state", content);
                contentJson = gson.toJson(state);
            } else {
                contentJson = gson.toJson(content);
            }

            //LOGGER.info("payload is: " + incomingCoapRequest.getPayloadString());
            //LOGGER.info("proxied content is: " + contentJson);

            HttpEntity entity = new ByteArrayEntity(contentJson.getBytes());
            ((HttpPost) httpRequest).setEntity(entity);

        }

        //LOGGER.info("iotCoreName: " + iotCoreName);

        HttpHost httpHost = new HttpHost("cloudiotdevice.googleapis.com", 443, "https");
        httpRequest.setHeader("authorization", String.format("Bearer %s", jwt_token));
        httpRequest.setHeader("cache-control", "no-cache");
        //httpRequest.setHeader(HttpHeaders.ACCEPT_ENCODING, "gzip");

        // DEBUG
        //httpHost = new HttpHost("localhost", 8000);
        //httpRequest = new HttpGet("hello.txt");

        //LOGGER.info(proxyUri.toString());
        //LOGGER.info(httpHost.toString());
        LOGGER.info(httpRequest.toString());

        asyncClient.execute(httpHost, httpRequest, new BasicHttpContext(), new FutureCallback<HttpResponse>() {
            @Override
            public void completed(HttpResponse result) {
                long timestamp = System.nanoTime();
                LOGGER.info("Received HTTP response: {}", result.getStatusLine());
                //LOGGER.info(result.toString());

                // HttpTranslator can't handle 'private' value
                result.setHeader("Cache-Control", "no-cache");

                // the entity of the response, if non repeatable, could be
                // consumed only one time, so do not debug it!
                // System.out.println(EntityUtils.toString(httpResponse.getEntity()));

                // translate the received http response in a coap response
                try {
                    Response coapResponse = new HttpTranslator().getCoapResponse(result, incomingCoapRequest);
                    coapResponse.setTimestamp(timestamp);

                    try {
                        GZIPInputStream gis = new GZIPInputStream(new ByteArrayInputStream(coapResponse.getPayload()));
                        InputStreamReader reader = new InputStreamReader(gis);
                        BufferedReader in = new BufferedReader(reader);
                        String decompressedPayload = in.lines().collect(Collectors.joining());
                        
                        Map map = gson.fromJson(decompressedPayload, Map.class);
                        if (map.containsKey("binaryData")) {
                            // base64-decode payload to send back to coap client in raw form
                            byte[] decodedPayload = Base64.getDecoder().decode(map.get("binaryData").toString());
                            coapResponse.setPayload(decodedPayload);
                        } else {
                            // no binaryData in response, so just send the original payload
                            coapResponse.setPayload(decompressedPayload);
                        }
                    } catch (IOException e) {
                        // do nothing if payload is not actually gzip compressed
                        LOGGER.info("Got IOException: {}", e.getMessage());
                    }

                    future.complete(coapResponse);
                } catch (InvalidFieldException e) {
                    LOGGER.warn("Problems during the http/coap translation: {}", e.getMessage());
                    future.complete(new Response(CoapTranslator.STATUS_FIELD_MALFORMED));
                } catch (TranslationException e) {
                    LOGGER.warn("Problems during the http/coap translation: {}", e.getMessage());
                    future.complete(new Response(CoapTranslator.STATUS_TRANSLATION_ERROR));
                }
            }

            @Override
            public void failed(Exception ex) {
                LOGGER.warn("Failed to get the http response: {}", ex.getMessage());
                future.complete(new Response(ResponseCode.INTERNAL_SERVER_ERROR));
            }

            @Override
            public void cancelled() {
                LOGGER.warn("Request canceled");
                future.complete(new Response(ResponseCode.SERVICE_UNAVAILABLE));
            }
        });


        return future;
    }
}
