package com.agosto.coap.dtls.client;

import org.eclipse.californium.core.coap.CoAP;
import org.eclipse.californium.core.coap.Request;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CoapRequestBuilderTest {

    @Test
    void build_GetRequest() {
        Request request = CoapRequestBuilder.build(CoapRequestBuilder.GET_METHOD);
        assertEquals(CoAP.Code.GET, request.getCode());
    }

    @Test
    void build_PostRequest() {
        Request request = CoapRequestBuilder.build(CoapRequestBuilder.POST_METHOD);
        assertEquals(CoAP.Code.POST, request.getCode());
    }

    @Test
    void build_PutRequest() {
        Request request = CoapRequestBuilder.build(CoapRequestBuilder.PUT_METHOD);
        assertEquals(CoAP.Code.PUT, request.getCode());
    }

    @Test
    void build_DeleteRequest() {
        Request request = CoapRequestBuilder.build(CoapRequestBuilder.DELETE_METHOD);
        assertEquals(CoAP.Code.DELETE, request.getCode());
    }

    @Test
    void build_ObserveRequest() {
        Request request = CoapRequestBuilder.build(CoapRequestBuilder.OBSERVE_METHOD);
        assertEquals(CoAP.Code.GET, request.getCode());
        assertTrue(request.isObserve());
    }

    @Test
    void build_DiscoverRequest() {
        Request request = CoapRequestBuilder.build(CoapRequestBuilder.DISCOVER_METHOD);
        assertEquals(CoAP.Code.GET, request.getCode());
    }
}