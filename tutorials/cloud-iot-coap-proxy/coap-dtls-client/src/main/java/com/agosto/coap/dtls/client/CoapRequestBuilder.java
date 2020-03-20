package com.agosto.coap.dtls.client;

import org.eclipse.californium.core.coap.Request;

/**
 * CoAP requests builder.
 */
class CoapRequestBuilder {

    static final String GET_METHOD = "GET";
    static final String POST_METHOD = "POST";
    static final String PUT_METHOD = "PUT";
    static final String DELETE_METHOD = "DELETE";
    static final String DISCOVER_METHOD = "DISCOVER";
    static final String OBSERVE_METHOD = "OBSERVE";

    /**
     * Build a new CoAP request, based on the method string passed into the method.
     *
     * @param method
     * @return
     */
    static Request build(String method) {
        Request request = null;
        switch (method) {
            case GET_METHOD:
                request = Request.newGet();
                break;
            case POST_METHOD:
                request = Request.newPost();
                break;
            case PUT_METHOD:
                request = Request.newPut();
                break;
            case DELETE_METHOD:
                request = Request.newDelete();
                break;
            case DISCOVER_METHOD:
                request = Request.newGet();
                break;
            case OBSERVE_METHOD:
                request = Request.newGet();
                request.setObserve();
                break;
        }
        return request;
    }
}
