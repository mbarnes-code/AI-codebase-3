#!/bin/bash

# Generate self-signed SSL certificate for development
mkdir -p ./Jane/monitoring/ssl

# Generate private key
openssl genrsa -out ./Jane/monitoring/ssl/jane.key 2048

# Generate certificate signing request
openssl req -new -key ./Jane/monitoring/ssl/jane.key -out ./Jane/monitoring/ssl/jane.csr -subj "/C=US/ST=Local/L=Development/O=Jane AI Platform/OU=Development/CN=jane.local"

# Generate self-signed certificate
openssl x509 -req -days 365 -in ./Jane/monitoring/ssl/jane.csr -signkey ./Jane/monitoring/ssl/jane.key -out ./Jane/monitoring/ssl/jane.crt

# Clean up CSR file
rm ./Jane/monitoring/ssl/jane.csr

echo "SSL certificates generated for jane.local"
echo "Add 'jane.local' to your /etc/hosts file pointing to 127.0.0.1"
