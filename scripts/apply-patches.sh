#!/bin/bash
# Apply GOAT A3000 LiDAR (cr0e4u) patches to the home-assistant container.
set -e

REPO_DIR="$(dirname "$0")/.."
CONTAINER=home-assistant
SITE=/usr/local/lib/python3.14/site-packages/deebot_client

docker cp "$REPO_DIR/patches/cr0e4u.py"             $CONTAINER:$SITE/hardware/cr0e4u.py
docker cp "$REPO_DIR/patches/clean.py"              $CONTAINER:$SITE/commands/json/clean.py
docker cp "$REPO_DIR/patches/messages_json_init.py" $CONTAINER:$SITE/messages/json/__init__.py

docker exec $CONTAINER rm -rf \
  $SITE/hardware/__pycache__ \
  $SITE/commands/json/__pycache__ \
  $SITE/messages/json/__pycache__

docker restart $CONTAINER
echo "$(date): patches applied, HA restarted"
