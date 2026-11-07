#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

# Build the same JavaScript sources without requiring npm in the Ruby container.
sources=(
  assets/js/plugins/jquery.greedy-navigation.js
  assets/js/_main.js
  assets/js/theme.js
)
for source_file in "${sources[@]}"; do
  cat "$source_file"
  printf '\n;\n'
done > assets/js/main.min.js
node --check assets/js/main.min.js

export JEKYLL_ENV=preview
exec bundle exec jekyll serve \
  --host 0.0.0.0 --port 4000 \
  --config _config.yml,_config_docker.yml --baseurl ""
