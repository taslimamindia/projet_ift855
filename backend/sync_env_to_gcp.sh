#!/bin/bash

# --- CONFIGURATION ---
ENV_FILE="gcloud.prod.env"
PROJECT_ID="project-ift855"

# --- FUNCTION TO UPLOAD SECRETS ---
update_secret() {
    local name=$1
    local source=$2

    # 1. VALIDATION: Check for invalid characters (spaces, special chars)
    if [[ ! "$name" =~ ^[a-zA-Z_0-9]+$ ]]; then
        echo "   ⚠️  SKIPPING '$name': Invalid characters. Secret IDs must be alphanumeric."
        return
    fi

    echo -n "   Processing: $name ... "

    # 2. CHECK EXISTENCE (Silently)
    # Added --quiet to prevent interactive prompts
    if gcloud secrets describe "$name" --project "$PROJECT_ID" --quiet > /dev/null 2>&1; then
        # --- SECRET EXISTS: ADD NEW VERSION ---
        printf "%s" "$source" | gcloud secrets versions add "$name" --project "$PROJECT_ID" --data-file=- --quiet > /dev/null 2>&1
        echo "✅ Updated (New Version)"
    else
        # --- SECRET MISSING: CREATE NEW ---
        printf "%s" "$source" | gcloud secrets create "$name" --project "$PROJECT_ID" --data-file=- --quiet > /dev/null 2>&1
        echo "✨ Created"
    fi
}

echo ""
echo "🚀 STARTING SECRET SYNCHRONIZATION"
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

        # TRIM WHITESPACE (Fixes the "Invalid Format" error)
        key=$(echo "$key" | xargs) 
        value=$(echo "$value" | xargs)

        # Remove quotes around value if they exist
        value=${value%\"}
        value=${value#\"}
        value=${value%\'}
        value=${value#\'}

        if [[ -n "$key" ]]; then
            update_secret "$key" "$value"
        fi

    done < "$ENV_FILE"
else
    echo "⚠️  File $ENV_FILE not found."
fi

echo "-------------------------------------"
echo "🎉 SYNC COMPLETED!"