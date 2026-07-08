#!/bin/bash

# Default commit message if none is provided as argument
COMMIT_MSG="${1:-Update codebase}"

echo "=== Staging all changes ==="
git add .

echo "=== Committing changes ==="
git commit -m "$COMMIT_MSG"

echo "=== Pushing to remote main branch ==="
git push origin main

echo "=== Upload complete! ==="
