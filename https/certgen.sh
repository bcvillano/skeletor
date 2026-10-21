#!/bin/bash

mkdir -p ./certs

openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ./certs/key.pem \
  -out ./certs/cert.pem \
  -days 365 \
  -subj "/CN=skeletor/O=skeletor/C=US"

echo "Self signed certificate and key generated and stored in ./https/certs/"