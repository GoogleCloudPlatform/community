/*******************************************************************************
 * Copyright (c) 2017 Bosch Software Innovations GmbH and others.
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
 *    Bosch Software Innovations GmbH - initial implementation
 ******************************************************************************/

package com.agosto.iot;

import org.eclipse.californium.scandium.config.DtlsConnectorConfig;
import org.eclipse.californium.scandium.dtls.pskstore.InMemoryPskStore;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Credentials utility for setup DTLS credentials.
 */
public class CredentialsUtil {

    /**
     * Credentials mode.
     */
    public enum Mode {
        /**
         * Preshared secret keys.
         */
        PSK,
        /**
         * Raw public key certificates.
         */
        RPK,
        /**
         * X.509 certificates.
         */
        X509,
        /**
         * raw public key certificates just trusted (client only).
         */
        RPK_TRUST,
        /**
         * X.509 certificates just trusted (client only).
         */
        X509_TRUST,
        /**
         * No client authentication (server only).
         */
        NO_AUTH,
    }

    /**
     * Default list of modes.
     * <p>
     * Value is PSK, RPK, X509.
     */
    static final List<Mode> DEFAULT_MODES = Arrays.asList(Mode.PSK, Mode.RPK, Mode.X509);

    /**
     * Parse arguments to modes.
     *
     * @param args      arguments
     * @param defaults  default modes to use, if argument is empty or only
     *                  contains {@link Mode#NO_AUTH}.
     * @param supported supported modes
     * @return array of modes.
     */
    static List<Mode> parse(String[] args, List<Mode> defaults, List<Mode> supported) {
        List<Mode> modes;
        if (args.length == 0) {
            modes = new ArrayList<>();
            if (defaults != null) {
                modes.addAll(defaults);
            }
        } else {
            modes = new ArrayList<>(args.length);
            for (String mode : args) {
                try {
                    modes.add(Mode.valueOf(mode));
                } catch (IllegalArgumentException ex) {
                    throw new IllegalArgumentException(String.format("Argument '%s' unkown!", mode));
                }
            }
        }
        if (supported != null) {
            for (Mode mode : modes) {
                if (!supported.contains(mode)) {
                    throw new IllegalArgumentException(String.format("Mode '%s' not supported!", mode));
                }
            }
        }
        // adjust default for "NO_AUTH"
        if (defaults != null && modes.size() == 1 && modes.contains(Mode.NO_AUTH)) {
            modes.addAll(defaults);
        }
        return modes;
    }

    /**
     * Setup credentials for DTLS connector.
     * <p>
     * If PSK is provided and no PskStore is already set for the builder, a
     * {@link InMemoryPskStore} containing PSK identity assigned with
     * PSK secret is set. If PSK is provided with other mode(s) and
     * loading the certificates failed, this is just treated as warning and the
     * configuration is setup to use PSK only.
     * <p>
     * If RPK is provided, the certificates loaded for the provided alias and
     * this certificate is used as identity.
     * <p>
     * If X509 is provided, the trusts are also loaded an set additionally to
     * the credentials for the alias.
     * <p>
     * The Modes can be mixed. If RPK is before X509 in the list, RPK is set as
     * preferred.
     * <p>
     * Examples:
     *
     * <pre>
     * PSK, RPK setup for PSK an RPK.
     * RPK, X509 setup for RPK and X509, prefer RPK
     * PSK, X509, RPK setup for PSK, RPK and X509, prefer X509
     * </pre>
     *
     * @param config      DTLS configuration builder. May be already initialized with
     *                    PskStore.
     * @param modes       list of supported mode. If a RPK is in the list before X509,
     *                    or RPK is provided but not X509, then the RPK is setup as
     *                    preferred.
     * @param pskIdentity String representing the pre-shared identity.
     * @param pskSecret   String representing the pre-shared secret.
     * @throws IllegalArgumentException if loading the certificates fails for
     *                                  some reason
     */
    static void setupCredentials(DtlsConnectorConfig.Builder config,
                                 List<Mode> modes,
                                 String pskIdentity,
                                 String pskSecret) {
        boolean psk = modes.contains(Mode.PSK);
        if (psk && config.getIncompleteConfig().getPskStore() == null) {
            InMemoryPskStore pskStore = new InMemoryPskStore();
            pskStore.setKey(pskIdentity, pskSecret.getBytes());
            config.setPskStore(pskStore);
        }
    }
}
