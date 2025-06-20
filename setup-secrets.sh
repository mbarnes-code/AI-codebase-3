#!/bin/bash
# setup-secrets.sh - Generate secrets for the AI Second Brain Platform

set -euo pipefail

SECRETS_DIR="./secrets"
ENV_FILE=".env"

echo "🔐 Setting up secrets for AI Second Brain Platform..."

# Create secrets directory if it doesn't exist
mkdir -p "$SECRETS_DIR"

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate hex key
generate_hex_key() {
    openssl rand -hex 32
}

# Generate secrets
echo "$(generate_password)" > "$SECRETS_DIR/postgres_password.txt"
echo "$(generate_password)" > "$SECRETS_DIR/redis_password.txt"
echo "$(generate_hex_key)" > "$SECRETS_DIR/django_secret_key.txt"
echo "$(generate_hex_key)" > "$SECRETS_DIR/n8n_encryption_key.txt"
echo "$(generate_hex_key)" > "$SECRETS_DIR/jwt_secret.txt"
echo "placeholder-api-key-replace-with-real" > "$SECRETS_DIR/llm_api_key.txt"

# Set proper permissions
chmod 600 "$SECRETS_DIR"/*.txt

# Create .env file from template
if [ ! -f "$ENV_FILE" ]; then
    cp .env.template "$ENV_FILE"
    echo "📝 Created $ENV_FILE from template"
    echo "⚠️  Please edit $ENV_FILE with your actual configuration values"
else
    echo "✅ $ENV_FILE already exists"
fi

# Create gitignore for secrets if not exists
if ! grep -q "secrets/\*.txt" .gitignore 2>/dev/null; then
    echo "secrets/*.txt" >> .gitignore
    echo "📝 Added secrets to .gitignore"
fi

echo "✅ Secrets generated successfully!"
echo "📁 Secret files created in $SECRETS_DIR/"
echo "🔒 Remember to update LLM_API_KEY in $SECRETS_DIR/llm_api_key.txt with your actual API key"
