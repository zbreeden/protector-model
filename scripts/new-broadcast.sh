#!/usr/bin/env bash
set -euo pipefail

echo "📡 Create a new FourTwenty Analytics signal broadcast"
echo "This generates a signals/latest.json file conforming to latest.schema.yml"
echo

# Helper function to get module info from seeds/modules.yml
get_module_info() {
    local module_key="$1"
    local field="$2"
    
    if [ ! -f "seeds/modules.yml" ]; then
        echo ""
        return
    fi
    
    # Extract module info using awk
    awk -v key="$module_key" -v field="$field" '
    BEGIN { found=0; in_module=0 }
    /^- id: / { 
        if ($3 == key) { found=1; in_module=1 } 
        else { in_module=0 }
    }
    in_module && $0 ~ "^  " field ": " { 
        gsub(/^  [^:]+: /, "")
        gsub(/^"/, "")
        gsub(/"$/, "")
        print
        exit
    }
    ' seeds/modules.yml
}

# Get and validate broadcast key (snake_case)
while :; do
    read -rp "Broadcast key (snake_case, e.g., 'big_bang', 'weekly_update'): " BROADCAST_KEY
    if [ -z "$BROADCAST_KEY" ]; then
        echo "❌ Broadcast key cannot be empty. Please try again."
        continue
    fi
    if ! printf "%s" "$BROADCAST_KEY" | grep -Eq '^[a-z0-9_]+$'; then
        echo "❌ Invalid broadcast key. Use lowercase letters, digits, and underscores only. Please try again."
        continue
    fi
    break
done

# Generate timestamp components
TS_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
TS_KEY=$(date -u +%Y%m%dT%H%M%SZ)
DATE_KEY=$(date -u +%Y-%m-%d)
BROADCAST_ID="${TS_KEY}-${BROADCAST_KEY}"

echo "🕐 Generated timestamp: $TS_UTC"
echo "🆔 Generated ID: $BROADCAST_ID"
echo

# Get and validate module key
echo "Available modules (from seeds/modules.yml):"
if [ -f "seeds/modules.yml" ]; then
    grep "^- id: " seeds/modules.yml | sed 's/^- id: /  /'
else
    echo "  (seeds/modules.yml not found - you can enter any module key)"
fi
echo


while :; do
    read -rp "Module key (snake_case, e.g., 'fourtwenty_analytics'): " MODULE_KEY
    if [ -z "$MODULE_KEY" ]; then
        echo "❌ Module key cannot be empty. Please try again."
        continue
    fi
    if ! printf "%s" "$MODULE_KEY" | grep -Eq '^[a-z0-9_]+$'; then
        echo "❌ Invalid module key. Use lowercase letters, digits, and underscores only. Please try again."
        continue
    fi
    # Check if module exists in seeds/modules.yml
    if [ -f "seeds/modules.yml" ] && ! grep -q "^- id: $MODULE_KEY$" seeds/modules.yml; then
        echo "⚠️ Module key '$MODULE_KEY' not found in seeds/modules.yml, but proceeding anyway."
    fi
    break
done

# Ask for broadcasting star's status (all from statuses.yml)
echo
STATUS_FILE="seeds/statuses.yml"
STATUS_IDS=()
STATUS_LABELS=()
if [ -f "$STATUS_FILE" ]; then
    echo "Available statuses from $STATUS_FILE:" 
    while IFS= read -r line; do
        if [[ $line =~ ^-\ id:\ ([a-z0-9_]+) ]]; then
            STATUS_IDS+=("${BASH_REMATCH[1]}")
        fi
        if [[ $line =~ ^\ +label:\ "(.*)" ]]; then
            STATUS_LABELS+=("${BASH_REMATCH[1]}")
        fi
    done < "$STATUS_FILE"
    for i in "${!STATUS_IDS[@]}"; do
        printf "  %-12s -> %s\n" "${STATUS_IDS[$i]}" "${STATUS_LABELS[$i]:-}" 
    done
else
    echo "  (statuses.yml not found - you can enter any status key)"
fi
echo
while :; do
    read -rp "Status for broadcasting module: " MODULE_STATUS
    if [ ${#STATUS_IDS[@]} -eq 0 ] || [[ " ${STATUS_IDS[*]} " == *" $MODULE_STATUS "* ]]; then
        break
    fi
    echo "❌ Status must be one of: ${STATUS_IDS[*]}. Please try again."
done

# Get module info for populating fields
MODULE_NAME=$(get_module_info "$MODULE_KEY" "name")
MODULE_REPO=$(get_module_info "$MODULE_KEY" "repo_url" | sed 's|.*/||' | sed 's|\.git$||')
MODULE_EMOJI=$(get_module_info "$MODULE_KEY" "emoji")
MODULE_PAGES_URL=$(get_module_info "$MODULE_KEY" "pages_url")
MODULE_REPO_URL=$(get_module_info "$MODULE_KEY" "repo_url")

echo "📦 Found module info:"
echo "  Name: ${MODULE_NAME:-"(not found)"}"
echo "  Repo: ${MODULE_REPO:-"(not found)"}"
echo "  Emoji: ${MODULE_EMOJI:-"(not found)"}"
echo "  Pages URL: ${MODULE_PAGES_URL:-"(not found)"}"
echo

# Get title and summary
read -rp "Title: " TITLE
if [ -z "$TITLE" ]; then
    echo "❌ Title cannot be empty."
    exit 1
fi

read -rp "Summary: " SUMMARY
if [ -z "$SUMMARY" ]; then
    echo "❌ Summary cannot be empty."
    exit 1
fi

# Get single tag
read -rp "Tag (single tag - additional tags can be added manually later): " TAG
if [ -z "$TAG" ]; then
    TAG="broadcast"
    echo "  Using default tag: broadcast"
fi

# Get rating
echo "Available ratings:"
echo "  critical -> Critical importance"
echo "  high -> High importance"
echo "  normal -> Normal importance"
echo
while :; do
    read -rp "Rating (critical/high/normal): " RATING
    if [[ "$RATING" =~ ^(critical|high|normal)$ ]]; then
        break
    fi
    echo "❌ Rating must be 'critical', 'high', or 'normal'. Please try again."
done

# Get origin module (default to current module)
echo
echo "📍 Origin module (typically same as broadcast module):"
read -rp "Origin module key [press enter for '$MODULE_KEY']: " ORIGIN_KEY
if [ -z "$ORIGIN_KEY" ]; then
    ORIGIN_KEY="$MODULE_KEY"
fi

# Get origin module info

ORIGIN_NAME=$(get_module_info "$ORIGIN_KEY" "name")
ORIGIN_EMOJI=$(get_module_info "$ORIGIN_KEY" "emoji")
ORIGIN_PAGES_URL=$(get_module_info "$ORIGIN_KEY" "pages_url")
ORIGIN_REPO_URL=$(get_module_info "$ORIGIN_KEY" "repo_url")

# Fallback values if module not found
if [ -z "$ORIGIN_NAME" ]; then
    ORIGIN_NAME="$ORIGIN_KEY"
fi
if [ -z "$ORIGIN_EMOJI" ]; then
    ORIGIN_EMOJI="📡"
fi
if [ -z "$ORIGIN_PAGES_URL" ]; then
    ORIGIN_PAGES_URL="https://zbreeden.github.io/${ORIGIN_KEY//_/-}/"
fi
if [ -z "$ORIGIN_REPO_URL" ]; then
    ORIGIN_REPO_URL="https://github.com/zbreeden/${ORIGIN_KEY//_/-}"
fi

echo "📍 Using origin info:"
echo "  Name: $ORIGIN_NAME"
echo "  Emoji: $ORIGIN_EMOJI"
echo "  URL: $ORIGIN_PAGES_URL"
echo

# Generate the broadcast JSON
echo "🛠️ Generating broadcast JSON..."

# Convert module key to repo format (snake_case to kebab-case)
REPO_NAME="${MODULE_KEY//_/-}"

# Generate broadcast content

BROADCAST_JSON=$(cat <<EOF
{
    "id": "$BROADCAST_ID",
    "ts_utc": "$TS_UTC",
    "module": "${MODULE_NAME:-$MODULE_KEY}",
    "repo": "$REPO_NAME",
    "title": "$TITLE",
    "summary": "$SUMMARY",
    "rating": "$RATING",
    "origin": {
        "name": "$ORIGIN_NAME",
        "url": "$ORIGIN_PAGES_URL",
        "emoji": "$ORIGIN_EMOJI"
    },
    "status": "$MODULE_STATUS",
    "links": {
        "readme": "${ORIGIN_REPO_URL}#readme",
        "page": "$ORIGIN_PAGES_URL"
    },
    "payload": {
        "module_key": "$MODULE_KEY",
        "broadcast_key": "$BROADCAST_KEY",
        "tags": ["$TAG"]
    }
}
EOF
)

# Validate against schema if available
if [ -f "schemas/latest.schema.yml" ] && command -v jq >/dev/null 2>&1; then
    echo "🔍 Validating against schema..."
    if echo "$BROADCAST_JSON" | jq empty 2>/dev/null; then
        echo "  ✅ JSON syntax is valid"
        
        # Check required fields
        required_fields=("id" "ts_utc" "module" "repo" "title" "summary" "rating" "origin" "links" "payload")
        all_valid=true
        for field in "${required_fields[@]}"; do
            if echo "$BROADCAST_JSON" | jq -e ".$field" >/dev/null 2>&1; then
                echo "  ✅ Field: $field"
            else
                echo "  ❌ Missing field: $field"
                all_valid=false
            fi
        done
        
        if [ "$all_valid" = true ]; then
            echo "  ✅ All required fields present"
        else
            echo "  ⚠️ Some required fields missing - broadcast may not validate"
        fi
    else
        echo "  ❌ JSON syntax is invalid"
        echo "$BROADCAST_JSON" | jq . 2>&1 || true
        exit 1
    fi
else
    echo "  ⚠️ Schema validation skipped (schemas/latest.schema.yml not found or jq not available)"
fi

# Create signals directory if it doesn't exist
mkdir -p signals

# Archive existing latest.json if it exists
SIGNALS_FILE="signals/latest.json"
ARCHIVE_FILE="signals/archive.latest.json"

if [ -f "$SIGNALS_FILE" ]; then
    echo "📦 Archiving existing broadcast..."
    
    if [ -f "$ARCHIVE_FILE" ]; then
        # Archive file exists - insert existing latest.json at beginning of array
        echo "  📚 Adding to existing archive..."
        
        # Read existing latest.json and archive array
        EXISTING_BROADCAST=$(cat "$SIGNALS_FILE")
        EXISTING_ARCHIVE=$(cat "$ARCHIVE_FILE")
        
        # Insert existing broadcast at beginning of archive array
        NEW_ARCHIVE=$(echo "$EXISTING_ARCHIVE" | jq --argjson new_item "$EXISTING_BROADCAST" '. = [$new_item] + .')
        
        # Write updated archive
        echo "$NEW_ARCHIVE" > "$ARCHIVE_FILE"
        echo "  ✅ Existing broadcast archived ($(echo "$NEW_ARCHIVE" | jq '. | length') total broadcasts in archive)"
        
    else
        # No archive file exists - create new one with existing latest.json
        echo "  📚 Creating new archive..."
        
        EXISTING_BROADCAST=$(cat "$SIGNALS_FILE")
        NEW_ARCHIVE=$(echo "[]" | jq --argjson new_item "$EXISTING_BROADCAST" '. = [$new_item]')
        
        # Write new archive file
        echo "$NEW_ARCHIVE" > "$ARCHIVE_FILE"
        echo "  ✅ Archive created with existing broadcast"
    fi
else
    echo "📦 No existing broadcast to archive"
fi


# Write the new broadcast file
echo "$BROADCAST_JSON" | jq . > "$SIGNALS_FILE"

# Update the status for the broadcasting module in seeds/modules.yml
MODULES_FILE="seeds/modules.yml"
if [ -f "$MODULES_FILE" ]; then
    # Use awk to update the status for the correct module
    TMP_FILE="${MODULES_FILE}.tmp"
    awk -v key="$MODULE_KEY" -v newstatus="$MODULE_STATUS" '
    BEGIN {in_module=0}
    /^- id: / {
        if ($3 == key) {in_module=1} else {in_module=0}
    }
    in_module && /^  status:/ {
        sub(/^  status: .*/, "  status: " newstatus)
    }
    {print}
    ' "$MODULES_FILE" > "$TMP_FILE" && mv "$TMP_FILE" "$MODULES_FILE"
    echo "✅ Updated status for module $MODULE_KEY to $MODULE_STATUS in $MODULES_FILE"
else
    echo "⚠️ seeds/modules.yml not found, could not update module status."
fi

echo
echo "🎉 Broadcast created successfully!"
echo "   📁 File: $SIGNALS_FILE"
echo "   🆔 ID: $BROADCAST_ID"
echo "   📡 Module: ${MODULE_NAME:-$MODULE_KEY}"
echo "   ⭐ Rating: $RATING"
echo "   🏷️ Tag: $TAG"
echo
echo "📋 Next steps:"
echo "   1. Review the generated $SIGNALS_FILE"
echo "   2. Add additional tags manually if needed"
echo "   3. Customize payload section if desired"
echo "   4. Commit and push to trigger constellation updates"
echo
echo "💡 Additional tags can be added manually by editing the 'tags' array in the payload section."
echo "🔗 Part of the FourTwenty Analytics constellation signal broadcasting system"