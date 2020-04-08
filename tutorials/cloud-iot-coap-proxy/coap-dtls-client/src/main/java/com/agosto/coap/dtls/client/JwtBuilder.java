package com.agosto.coap.dtls.client;

import com.auth0.jwt.JWT;
import com.auth0.jwt.algorithms.Algorithm;
import com.auth0.jwt.exceptions.JWTCreationException;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.openssl.PEMKeyPair;
import org.bouncycastle.openssl.PEMParser;
import org.bouncycastle.openssl.jcajce.JcaPEMKeyConverter;

import java.io.InputStreamReader;
import java.io.Reader;
import java.security.KeyPair;
import java.security.Security;
import java.security.interfaces.ECPrivateKey;
import java.security.interfaces.ECPublicKey;
import java.util.Calendar;
import java.util.Date;

class JwtBuilder {

    String build(String projectId) {
        String token;
        Algorithm algorithm;
        try {
            Security.addProvider(new BouncyCastleProvider());
            Reader reader = new InputStreamReader(ClassLoader.getSystemResourceAsStream("ec_private.pem"));
            PEMParser pemParser = new PEMParser(reader);
            PEMKeyPair pemKeyPair = (PEMKeyPair) pemParser.readObject();
            KeyPair keyPair = new JcaPEMKeyConverter().getKeyPair(pemKeyPair);
            ECPrivateKey privateKey = (ECPrivateKey) keyPair.getPrivate();
            ECPublicKey publicKey = (ECPublicKey) keyPair.getPublic();
            algorithm = Algorithm.ECDSA256(publicKey, privateKey);
        } catch (Exception e) {
            throw new RuntimeException("Unable to retrieve the EC private key.", e);
        }

        try {
            Date now = new Date();
            Calendar cal = Calendar.getInstance();
            cal.setTime(now);
            cal.add(Calendar.HOUR_OF_DAY, 1);
            Date oneHourFromNow = cal.getTime();
            token = JWT.create().
                    withIssuer("auth0").
                    withAudience(projectId).
                    withIssuedAt(now).
                    withExpiresAt(oneHourFromNow).
                    sign(algorithm);
        } catch (JWTCreationException e) {
            throw new RuntimeException("Unable to create and sign JWT.", e);
        }
        return token;
    }
}
