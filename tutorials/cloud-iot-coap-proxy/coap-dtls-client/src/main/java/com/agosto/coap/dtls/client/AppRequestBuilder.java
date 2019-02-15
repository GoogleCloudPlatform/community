package com.agosto.coap.dtls.client;

import org.eclipse.californium.core.coap.Request;

import java.text.MessageFormat;

class AppRequestBuilder {
    // resource path in the form of ${GOOGLE_CLOUD_PROJECT}/${IOT_CORE_REGION}/${IOT_CORE_REGISTRY}"
    private static final String IOT_CORE_PATH = "IOT_CORE_PATH";

    static Request build(String method, String deviceId, String jwt) {
        Request request = null;
        String proxyUri = null;
        final String iotCorePath = System.getenv(IOT_CORE_PATH);
        if (iotCorePath == null || iotCorePath.length() == 0) {
            throw new RuntimeException("Environment variable IOT_CORE_PATH is not set.");
        }
        switch (method) {
            case "publishEvent":
                request = CoapRequestBuilder.build(CoapRequestBuilder.POST_METHOD);
                proxyUri = MessageFormat.format("{0}/{1}/publishEvent?jwt={2}", iotCorePath, deviceId, jwt);
                request.getOptions().setProxyUri(proxyUri);
                break;
            case "setState":
                request = CoapRequestBuilder.build(CoapRequestBuilder.POST_METHOD);
                proxyUri = MessageFormat.format("{0}/{1}/setState?jwt={2}", iotCorePath, deviceId, jwt);
                break;
            case "config":
                request = CoapRequestBuilder.build(CoapRequestBuilder.GET_METHOD);
                proxyUri = MessageFormat.format("{0}/{1}/config?jwt={2}", iotCorePath, deviceId, jwt);
                break;
        }
        if (request != null) {
            request.getOptions().setProxyUri(proxyUri);
        }
        return request;
    }
}
