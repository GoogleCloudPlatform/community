curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/le_cert" -H "Metadata-Flavor: Google" > nbcert.pem
curl "http://metadata.google.internal/computeMetadata/v1/instance/attributes/le_key" -H "Metadata-Flavor: Google" > nbkey.key

