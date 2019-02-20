package com.agosto.coap.dtls.client;


import org.eclipse.californium.core.Utils;
import org.eclipse.californium.core.coap.CoAP;
import org.eclipse.californium.core.coap.MediaTypeRegistry;
import org.eclipse.californium.core.coap.Request;
import org.eclipse.californium.core.coap.Response;
import org.eclipse.californium.core.network.CoapEndpoint;
import org.eclipse.californium.core.network.Endpoint;
import org.eclipse.californium.core.network.EndpointManager;
import org.eclipse.californium.core.network.config.NetworkConfig;
import org.eclipse.californium.scandium.DTLSConnector;
import org.eclipse.californium.scandium.config.DtlsConnectorConfig;
import org.eclipse.californium.scandium.dtls.cipher.CipherSuite;
import org.eclipse.californium.scandium.dtls.pskstore.InMemoryPskStore;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.URISyntaxException;
import java.security.GeneralSecurityException;
import java.text.MessageFormat;

/**
 * This class implements a simple CoAP client for testing purposes. Usage:
 * <p>
 * {@code java -jar coap-dtls-client-1.0-SNAPSHOT.jar DEVICE_ID METHOD URI [PAYLOAD]}
 * <ul>
 * <li>METHOD: {publishEvent, setState, config}
 * <li>URI: The URI to the remote endpoint or resource}
 * <li>PAYLOAD: The data to send with the request}
 * </ul>
 * Options:
 * <ul>
 * <li>-l: Loop for multiple responses}
 * </ul>
 */
public class ConsoleClient {

    // indices of command line parameters
    private static final int IDX_DEVICE_ID = 0;
    private static final int IDX_METHOD = 1;
    private static final int IDX_URI = 2;
    private static final int IDX_PAYLOAD = 3;

    // exit codes for runtime errors
    private static final int ERR_MISSING_METHOD = -1;
    private static final int ERR_UNKNOWN_METHOD = -2;
    private static final int ERR_MISSING_URI = -3;
    private static final int ERR_BAD_URI = -4;
    private static final int ERR_REQUEST_FAILED = -5;
    private static final int ERR_RESPONSE_FAILED = -6;

    private static final String PSK_IDENTITY = "PSK_IDENTITY";
    private static final String PSK_SECRET = "PSK_SECRET";
    private static final String IOT_CORE_PROJECT = "IOT_CORE_PROJECT";

    /*
     * Main method of this client.
     */
    public static void main(String[] args) throws IOException, GeneralSecurityException {
        String method = null;
        String deviceId = null;
        URI uri = null;
        String payload = "";
        Endpoint dtlsEndpoint;

        final String projectId = System.getenv(ConsoleClient.IOT_CORE_PROJECT);
        if (projectId == null || projectId.length() == 0) {
            throw new RuntimeException("Environment variable IOT_CORE_PROJECT is not set.");
        }

        final String pskIdentity = System.getenv(ConsoleClient.PSK_IDENTITY);
        if (pskIdentity == null || pskIdentity.length() == 0) {
            throw new RuntimeException("Environment variable PSK_IDENTITY is not set.");
        }
        final String pskSecret = System.getenv(ConsoleClient.PSK_SECRET);
        if (pskSecret == null || pskSecret.length() == 0) {
            throw new RuntimeException("Environment variable PSK_SECRET is not set.");
        }

        // display help if no parameters specified
        if (args.length == 0) {
            printInfo();
            return;
        }

        // input parameters
        int idx = 0;
        for (String arg : args) {
            switch (idx) {
                case IDX_DEVICE_ID:
                    deviceId = arg;
                    break;
                case IDX_METHOD:
                    method = arg;
                    break;
                case IDX_URI:
                    try {
                        uri = new URI(arg);
                    } catch (URISyntaxException e) {
                        System.err.println(MessageFormat.format("Failed to parse URI: {0}", e.getMessage()));
                        System.exit(ERR_BAD_URI);
                    }
                    break;
                case IDX_PAYLOAD:
                    payload = arg;
                    break;
                default:
                    System.out.println(MessageFormat.format("Unexpected argument: {0}", arg));
            }
            ++idx;
        }

        // check if mandatory parameters specified
        if (method == null) {
            System.err.println("Method not specified");
            System.exit(ERR_MISSING_METHOD);
        }
        if (uri == null) {
            System.err.println("URI not specified");
            System.exit(ERR_MISSING_URI);
        }
        String jwt = new JwtBuilder().build(projectId);
        Request request = AppRequestBuilder.build(method, deviceId, jwt);

        if (request == null) {
            System.err.println(MessageFormat.format("Unable to create CoAP request with method: {0}", method));
            System.exit(ERR_UNKNOWN_METHOD);
        }
        request.setURI(uri);
        request.getOptions().setContentFormat(MediaTypeRegistry.TEXT_PLAIN);
        if (payload != null) {
            request.setPayload(payload);
        }

        if (request.getScheme().equals(CoAP.COAP_SECURE_URI_SCHEME)) {
            InetSocketAddress inetSocketAddress = new InetSocketAddress(0);
            DtlsConnectorConfig.Builder builder = new DtlsConnectorConfig.Builder();
            builder.setAddress(inetSocketAddress);
            builder.setSupportedCipherSuites(new CipherSuite[]{CipherSuite.TLS_PSK_WITH_AES_128_CCM_8});
            byte[] secretKeyInBytes = pskSecret.getBytes();
            InMemoryPskStore pskStore = new InMemoryPskStore();
            InetSocketAddress peerAddress = request.getDestinationContext().getPeerAddress();
            pskStore.addKnownPeer(peerAddress, pskIdentity, secretKeyInBytes);
            pskStore.setKey(pskIdentity, secretKeyInBytes);
            builder.setPskStore(pskStore);
            DTLSConnector dtlsconnector = new DTLSConnector(builder.build(), null);
            dtlsEndpoint = new CoapEndpoint(dtlsconnector, NetworkConfig.getStandard());
            dtlsEndpoint.start();
            EndpointManager.getEndpointManager().setDefaultEndpoint(dtlsEndpoint);
        }
        try {
            request.send();
            Response response = null;
            try {
                response = request.waitForResponse();
            } catch (InterruptedException e) {
                System.err.println(MessageFormat.format("Failed to receive response: {0}", e.getMessage()));
                System.exit(ERR_RESPONSE_FAILED);
            }
            if (response != null) {
                System.out.println(Utils.prettyPrint(response));
                System.out.println(MessageFormat.format("Time elapsed (ms): {0}", response.getRTT()));
                if (response.getOptions().isContentFormat(MediaTypeRegistry.APPLICATION_LINK_FORMAT)) {
                    String linkFormat = response.getPayloadString();
                    System.out.println("\nDiscovered resources:");
                    System.out.println(linkFormat);
                } else {
                    if (method.equals("DISCOVER")) {
                        System.out.println("Server error: Link format not specified");
                    }
                }
            } else {
                System.err.println("Request timed out");
            }
        } catch (Exception e) {
            System.err.println(MessageFormat.format("Failed to execute request: {0}", e.getMessage()));
            System.exit(ERR_REQUEST_FAILED);
        }
    }

    /*
     * Outputs user guide of this program.
     */
    private static void printInfo() {
        String command = "java -jar ./target/coap-dtls-client-1.0-SNAPSHOT.jar";
        System.out.println();
        System.out.println(MessageFormat.format("Usage: {0} [-l] DEVICE_ID METHOD URI [PAYLOAD]",
                command));
        System.out.println("  DEVICE_ID  : The identifier for your IoT device");
        System.out.println("  METHOD     : {publishEvent, setState, config}");
        System.out.println("  URI        : The CoAP URI of the remote endpoint or resource");
        System.out.println("               A coaps URI will automatically use CoAP over DTLS");
        System.out.println("  PAYLOAD    : The data to send with the request");
        System.out.println();
        System.out.println("Examples:");
        System.out.println(MessageFormat.format("  {0} testing-device-001 config coaps://127.0.0.1:5684/gcp",
                command));
        System.out.println(MessageFormat.format("  {0} testing-device-001 publishEvent coaps://127.0.0.1:5684/gcp \"Event data\"",
                command));
    }
}
