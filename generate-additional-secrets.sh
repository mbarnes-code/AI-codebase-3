# Generate random authentik secret key
openssl rand -base64 32 > ./secrets/authentik_secret_key.txt

# Generate random authentik postgres password
openssl rand -base64 24 > ./secrets/authentik_postgres_password.txt

echo "Generated additional secret files for new services"
