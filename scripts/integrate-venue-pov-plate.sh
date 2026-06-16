#!/usr/bin/env bash
# Install a clean instrument POV venue background plate.
# Usage:
#   ./scripts/integrate-venue-pov-plate.sh guitar /path/to/clean-guitar-pov.png
#   ./scripts/integrate-venue-pov-plate.sh bass /path/to/clean-bass-pov.png
#   ./scripts/integrate-venue-pov-plate.sh drums /path/to/clean-drums-pov.png
#   ./scripts/integrate-venue-pov-plate.sh piano /path/to/clean-piano-pov.png
#   ./scripts/integrate-venue-pov-plate.sh vocals /path/to/clean-vocals-pov.png
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST_DIR="$ROOT/static/assets/venue/themes/small-club"
POV="${1:-}"
SOURCE="${2:-}"
MAX_WIDTH=1920
VALID_POVS="guitar bass drums piano vocals"

if [[ -z "$POV" || -z "$SOURCE" ]]; then
  echo "Usage: $0 <guitar|bass|drums|piano|vocals> /path/to/source.png" >&2
  exit 1
fi

case " $VALID_POVS " in
  *" $POV "*) ;;
  *)
    echo "Invalid POV: $POV (expected one of: $VALID_POVS)" >&2
    exit 1
    ;;
esac

if [[ ! -f "$SOURCE" ]]; then
  echo "Source image not found: $SOURCE" >&2
  exit 1
fi

OUT_PNG="$DEST_DIR/${POV}-pov-bg.png"
OUT_WEBP="$DEST_DIR/${POV}-pov-bg.webp"

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
