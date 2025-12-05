#!/bin/bash

# --- CONFIGURATION ---
ENV_FILE="github.prod.env"

# --- CHECK FOR GITHUB CLI ---
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI ('gh') is not installed."
    echo "   Please install it: https://cli.github.com/"
    echo "   Then login with: gh auth login"
    exit 1
fi

# --- FUNCTION TO UPLOAD SECRETS ---
update_github_secret() {
    local name=$1
    local value=$2

    echo -n "   Processing: $name ... "

    # Set the secret using GitHub CLI
    # We use stdin to pass the value to avoid issues with special characters in the shell
    # --app actions ensures it goes to Actions secrets (default, but good to be explicit if needed, though 'gh secret set' defaults to actions)
    echo "$value" | gh secret set "$name" --body - 

    if [ $? -eq 0 ]; then
        echo "✅ Updated"
    else
        echo "❌ Failed"
    fi
}

echo ""
echo "🚀 STARTING GITHUB SECRETS SYNCHRONIZATION"
echo "-------------------------------------"

# --- PROCESS .ENV FILE ---
if [ -f "$ENV_FILE" ]; then
    echo "📂 Reading $ENV_FILE..."
    
    # Read line by line
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments (#) and empty lines
        if [[ "$line" =~ ^\s*# ]] || [[ -z "$line" ]]; then
            continue
        fi

        # Remove 'export ' if present
        line=${line#export }

        # Extract Key and Value (split by first =)
        key=$(echo "$line" | cut -d '=' -f 1)
        value=$(echo "$line" | cut -d '=' -f 2-)

        # TRIM WHITESPACE
        key=$(echo "$key" | xargs) 
        value=$(echo "$value" | xargs)

        # Remove quotes around value if they exist
        value=${value%\"}
        value=${value#\"}
        value=${value%\'}
        value=${value#\'}

        if [[ -n "$key" ]]; then
            update_github_secret "$key" "$value"
        fi

    done < "$ENV_FILE"
else
    echo "⚠️  File $ENV_FILE not found."
fi

echo "-------------------------------------"
echo "🎉 SYNC COMPLETED!"
