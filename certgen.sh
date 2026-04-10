#!/bin/bash

mkdir -p ./https/certs

openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout ./https/certs/key.pem \
  -out ./https/certs/cert.pem \
  -days 365 \
  -subj "/CN=skeletor/O=skeletor/C=US"

echo "Self signed certificate and key generated and stored in ./https/certs/"