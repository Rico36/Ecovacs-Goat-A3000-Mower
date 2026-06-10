#!/bin/bash
# Hourly cron: reapply GOAT A3000 patches if a container update wiped them.
# Does nothing if patches are intact. Run as root (docker access).

CONTAINER=home-assistant
SITE=/usr/local/lib/python3.14/site-packages/deebot_client
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Skip silently if the container isn't running
docker inspect -f '{{.State.Running}}' $CONTAINER 2>/dev/null | grep -q true || exit 0

# Sentinel: stock cr0e4u.py has no CleanMower. If it's present, patches are intact.
if docker exec $CONTAINER grep -q "CleanMower" $SITE/hardware/cr0e4u.py 2>/dev/null; then
  exit 0
fi

"$REPO_DIR/scripts/apply-patches.sh"
echo "$(date): patches were wiped - reapplied and restarted HA"
