package com.agosto.coap.dtls.client;

import com.auth0.jwt.JWT;
import com.auth0.jwt.JWTVerifier;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.interfaces.DecodedJWT;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.openssl.PEMKeyPair;
import org.bouncycastle.openssl.PEMParser;
import org.bouncycastle.openssl.jcajce.JcaPEMKeyConverter;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.InputStreamReader;
import java.io.Reader;
import java.security.KeyPair;
import java.security.Security;
import java.security.interfaces.ECPrivateKey;
import java.security.interfaces.ECPublicKey;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class JwtBuilderTests {

    private JwtBuilder jwtBuilder;
    private JWTVerifier verifier;

    @BeforeEach
    void beforeEachTest() {
        try {
            Security.addProvider(new BouncyCastleProvider());
            Reader reader = new InputStreamReader(ClassLoader.getSystemResourceAsStream("ec_private.pem"));
            PEMParser pemParser = new PEMParser(reader);
            PEMKeyPair pemKeyPair = (PEMKeyPair) pemParser.readObject();
            KeyPair keyPair = new JcaPEMKeyConverter().getKeyPair(pemKeyPair);
            ECPrivateKey privateKey = (ECPrivateKey) keyPair.getPrivate();
            ECPublicKey publicKey = (ECPublicKey) keyPair.getPublic();
            Algorithm algorithm = Algorithm.ECDSA256(publicKey, privateKey);
            verifier = JWT.require(algorithm).withIssuer("auth0").build();
        } catch (Exception e) {
            throw new RuntimeException("Unable to retrieve the EC private key.", e);
        }

        jwtBuilder = new JwtBuilder();
    }

    @Test
    void build_Successful() {
        String token = jwtBuilder.build("coap-iot-core");
        assertNotNull(token);
        DecodedJWT jwt = verifier.verify(token);
        assertEquals("coap-iot-core", jwt.getAudience().get(0));
    }
}
