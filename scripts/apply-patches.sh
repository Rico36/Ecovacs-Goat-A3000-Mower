#!/bin/bash
# Apply GOAT A3000 LiDAR (cr0e4u) patches to the home-assistant container.
set -e

REPO_DIR="$(dirname "$0")/.."
CONTAINER=home-assistant
SITE=/usr/local/lib/python3.14/site-packages/deebot_client

# Patches are full-file replacements built against this exact library
# version. Applying them over another version would silently revert
# unrelated upstream changes.
WANT="18.3.0"
GOT=$(docker exec $CONTAINER python -c "import deebot_client; print(deebot_client.__version__)" 2>/dev/null)
if [ "$GOT" != "$WANT" ]; then
  echo "deebot-client $GOT found, patches were built for $WANT. Aborting."
  echo "Diff the patches against your installed files and port by hand."
  exit 1
fi

docker cp "$REPO_DIR/patches/cr0e4u.py"             $CONTAINER:$SITE/hardware/cr0e4u.py
docker cp "$REPO_DIR/patches/clean.py"              $CONTAINER:$SITE/commands/json/clean.py
docker cp "$REPO_DIR/patches/messages_json_init.py" $CONTAINER:$SITE/messages/json/__init__.py

docker exec $CONTAINER rm -rf \
  $SITE/hardware/__pycache__ \
  $SITE/commands/json/__pycache__ \
  $SITE/messages/json/__pycache__

docker restart $CONTAINER
echo "$(date): patches applied, HA restarted"
