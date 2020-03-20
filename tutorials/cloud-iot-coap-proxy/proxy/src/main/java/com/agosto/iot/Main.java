/*******************************************************************************
 * Copyright (c) 2015 Institute for Pervasive Computing, ETH Zurich and others.
 * 
 * All rights reserved. This program and the accompanying materials
 * are made available under the terms of the Eclipse Public License v1.0
 * and Eclipse Distribution License v1.0 which accompany this distribution.
 * 
 * The Eclipse Public License is available at
 *    http://www.eclipse.org/legal/epl-v10.html
 * and the Eclipse Distribution License is available at
 *    http://www.eclipse.org/org/documents/edl-v10.html.
 * 
 * Contributors:
 *    Matthias Kovatsch - creator and main architect
 ******************************************************************************/
package com.agosto.iot;

import com.agosto.iot.CredentialsUtil.Mode;
import org.eclipse.californium.core.CoapResource;
import org.eclipse.californium.core.CoapServer;
import org.eclipse.californium.core.network.CoapEndpoint;
import org.eclipse.californium.core.network.EndpointManager;
import org.eclipse.californium.core.network.config.NetworkConfig;
import org.eclipse.californium.core.server.resources.CoapExchange;
import org.eclipse.californium.proxy.resources.ForwardingResource;
import org.eclipse.californium.scandium.DTLSConnector;
import org.eclipse.californium.scandium.config.DtlsConnectorConfig;

import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.text.MessageFormat;
import java.util.Arrays;
import java.util.List;

/**
 * Http2CoAP: Insert in browser:
 *     URI: http://localhost:8080/proxy/coap://localhost:PORT/target
 * 
 * CoAP2CoAP: Insert in Copper:
 *     URI: coap://localhost:PORT/coap2coap
 *     Proxy: coap://localhost:PORT/targetA
 *
 * CoAP2Http: Insert in Copper:
 *     URI: coap://localhost:PORT/coap2http
 *     Proxy: http://lantersoft.ch/robots.txt
 */
public class Main {
	private static final List<Mode> SUPPORTED_MODES = Arrays
			.asList(Mode.PSK, Mode.RPK, Mode.X509, Mode.NO_AUTH);
	private static final int PORT = NetworkConfig.getStandard().getInt(NetworkConfig.Keys.COAP_PORT);
	private static final int DTLS_PORT = NetworkConfig.getStandard().getInt(NetworkConfig.Keys.COAP_SECURE_PORT);

	private static CoapServer server;

	public static void main(String[] args) {
		final String pskIdentity = System.getenv("PSK_IDENTITY");
		if (pskIdentity == null || pskIdentity.length() == 0) {
			throw new RuntimeException("Environment variable PSK_IDENTITY has not been set.");
		}
		final String pskSecret = System.getenv("PSK_SECRET");
		if (pskSecret == null || pskSecret.length() == 0) {
			throw new RuntimeException("Environment variable PSK_SECRET has not been set.");
		}

		ForwardingResource coap2http = new IotCoreForwardingResource("gcp");
		server = new CoapServer(PORT);
		server.add(coap2http);
		server.add(new TargetResource("info"));

		DtlsConnectorConfig.Builder config = new DtlsConnectorConfig.Builder();
		config.setAddress(new InetSocketAddress(DTLS_PORT));
		List<Mode> modes = CredentialsUtil.parse(args, CredentialsUtil.DEFAULT_MODES, SUPPORTED_MODES);
		CredentialsUtil.setupCredentials(config, modes, pskIdentity, pskSecret);
		DTLSConnector connector = new DTLSConnector(config.build());
		CoapEndpoint.CoapEndpointBuilder builder = new CoapEndpoint.CoapEndpointBuilder();
		builder.setConnector(connector);
		server.addEndpoint(builder.build());
		server.start();
	}
	
	/**
	 * A simple resource that responds to GET requests with a small response
	 * containing the resource's name.
	 */
	private static class TargetResource extends CoapResource {
		
		private int counter = 0;
		
		TargetResource(String name) {
			super(name);
		}
		
		@Override
		public void handleGET(CoapExchange exchange) {
			exchange.respond(MessageFormat.format("Response {0} from resource {1}", ++counter, getName()));
		}
	}
}
