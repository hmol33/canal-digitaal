#!/bin/bash

# Adapted from https://gist.github.com/domenic/ec8b0fc8ab45f39403dd

set -euo pipefail

if [ "${GITHUB_ACTIONS:-}" = "true" ] && [ "${GITHUB_EVENT_NAME:-}" = "pull_request" ]; then
    # don't run for PRs
    exit 0
fi

CWD=$(pwd)
SOURCE_BRANCH="master"
TARGET_BRANCH="gh-pages"

BUILD_DIR="$HOME/.build"
SOURCES_DIR="$HOME/.sources"
REPO=$(git config remote.origin.url)
SSH_REPO=${REPO/https:\/\/github.com\//git@github.com:}
SHA=$(git rev-parse --verify HEAD)

REPO_USER=$(echo "${GITHUB_REPOSITORY:-}" | grep -Eo '^([^/]+)' || echo "")
REPO_NAME=$(echo "${GITHUB_REPOSITORY:-}" | grep -Eo '([^/]+)$' || echo "")

if [ -z "$REPO_USER" ] || [ -z "$REPO_NAME" ]; then
    echo "ERROR: GITHUB_REPOSITORY not set or invalid"
    exit 1
fi

DATADIR='datadir'

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "Starting canal-digitaal build for $REPO_USER/$REPO_NAME"

git clone --quiet "$REPO" "$BUILD_DIR"

cd "$BUILD_DIR"
git checkout "$TARGET_BRANCH" 2>/dev/null || git checkout --orphan "$TARGET_BRANCH"

cd "$CWD"
# Clean out existing contents
rm -rf "$BUILD_DIR"/* || exit 1
rm -rf "$BUILD_DIR/.github" "$BUILD_DIR/.travis.yml" "$BUILD_DIR/.gitignore" || exit 1

# Download create_repository.py
create_repo_script_url='https://raw.githubusercontent.com/chadparry/kodi-repository.chad.parry.org/master/tools/create_repository.py'
create_repository_py='.github/create_repository.py'
log "Downloading create_repository.py"
wget -q -t 2 -O "$create_repository_py" "$create_repo_script_url" || curl --retry 2 -o "$create_repository_py" "$create_repo_script_url"

# Download jq
jq_url='https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64'
jq_path='.github/jq'
log "Downloading jq"
wget -q -t 2 -O "$jq_path" "$jq_url" || curl --retry 2 -o "$jq_path" "$jq_url"
chmod +x "$jq_path"

# Iterate through config.json and clone each branch
# - Generate a repo addon for each branch
#   - repo addon will include all the branches
# - Generate a repo set of addons.xml, addons.xml.md5 etc for each branch
for b in $(cat .github/config.json | .github/jq -c .branchmap[]); do
    name=$(echo "$b" | .github/jq -r '.name')
    minversion=$(echo "$b" | .github/jq -r '.minversion')
    log "Processing branch: $name (minversion: $minversion)"
    mkdir -p "$SOURCES_DIR/$name" "$SOURCES_DIR/$DATADIR"

    git clone --quiet --depth 1 "$REPO" -b "$name" "$SOURCES_DIR/$name"

    python3 .github/build_repo_addon.py "$REPO_USER" "$REPO_NAME" "$SOURCES_DIR/$name/src/" -t '.github/templates/repo.addon.xml.tmpl' -c '.github/config.json' -d "$DATADIR" --icon '.github/templates/icon.png' --fanart '.github/templates/fanart.jpg'

    # Do our repo build
    plugin_sources=''
    for d in "$SOURCES_DIR/$name/src/"* ; do
        if [ -d "$d" ]; then
            if [ ! -z "$plugin_sources" ]; then
                # Append a space
                plugin_sources="$plugin_sources "
            fi
            plugin_sources="$plugin_sources$d"
        fi
    done
    mkdir -p "$BUILD_DIR/$name/" "$BUILD_DIR/$name/$DATADIR/"
    python3 "$create_repository_py" -d "$BUILD_DIR/$name/$DATADIR/" -i "$BUILD_DIR/$name/addons.xml" -c "$BUILD_DIR/$name/addons.xml.md5" $plugin_sources

done

# Generate readme.md
log "Generating README.md"
python3 .github/build_readme.py "$REPO_USER" "$REPO_NAME" ".github/config.json" "$SHA" -t ".github/templates/repo.readme.md.tmpl" -o "$BUILD_DIR/README.md" -d "$DATADIR" -b "$BUILD_DIR"

cd "$BUILD_DIR"
git config user.name "GitHub Actions"
git config user.email "actions@github.com"

if git diff --quiet; then
    echo "No changes to the output on this push; exiting."
    exit 0
fi

git add -A .
git commit -m "Deploy to GitHub Pages: ${SHA}"

# Push to gh-pages branch
log "Pushing to $TARGET_BRANCH"
git push --quiet "$SSH_REPO" "$TARGET_BRANCH"

echo "Published to GitHub Pages https://$REPO_USER.github.io/$REPO_NAME/"
