#!/usr/bin/env bash
# Integrate the generated small-club venue background plate into the repo.
# Usage:
#   ./scripts/integrate-venue-bg-plate.sh /path/to/a_wide_cinematic_view_of_a_live_rock_club_stage_v.png
# Or copy the source PNG into the theme folder first:
#   ./scripts/integrate-venue-bg-plate.sh static/assets/venue/themes/small-club/a_wide_cinematic_view_of_a_live_rock_club_stage_v.png
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST_DIR="$ROOT/static/assets/venue/themes/small-club"
SOURCE="${1:-$DEST_DIR/a_wide_cinematic_view_of_a_live_rock_club_stage_v.png}"
OUT_PNG="$DEST_DIR/bg-plate.png"
OUT_WEBP="$DEST_DIR/bg-plate.webp"
MAX_WIDTH=1920

if [[ ! -f "$SOURCE" ]]; then
  echo "Source image not found: $SOURCE" >&2
  echo "Copy the generated PNG into the repo, then re-run this script." >&2
  exit 1
fi

if ! command -v sips >/dev/null 2>&1; then
  echo "sips not found; copying source without resize." >&2
  cp "$SOURCE" "$OUT_PNG"
else
  cp "$SOURCE" "$OUT_PNG"
  WIDTH="$(sips -g pixelWidth "$OUT_PNG" 2>/dev/null | awk '/pixelWidth/ {print $2}')"
  if [[ -n "${WIDTH:-}" && "$WIDTH" -gt "$MAX_WIDTH" ]]; then
    sips -Z "$MAX_WIDTH" "$OUT_PNG" >/dev/null
  fi
fi

if command -v cwebp >/dev/null 2>&1; then
  cwebp -q 82 "$OUT_PNG" -o "$OUT_WEBP" >/dev/null
  echo "Created WebP: $OUT_WEBP"
else
  echo "cwebp not available; PNG only."
fi

echo "Created PNG: $OUT_PNG"
sips -g pixelWidth -g pixelHeight "$OUT_PNG" 2>/dev/null || file "$OUT_PNG"
ls -lh "$OUT_PNG" "${OUT_WEBP:-/dev/null}" 2>/dev/null || ls -lh "$OUT_PNG"
