#!/bin/bash -e

readonly THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
readonly TAG_REPOS=" \
    poky \
    meta-mender \
"
# Repos using yocto-<major.minor>.<patch> tags instead of codename-prefixed ones
readonly YOCTO_TAG_REPOS=" poky "

function help() {
    cat <<EOF
Usage: $(basename "${BASH_SOURCE[0]}") repo.conf

Options:
  -h, --help      Print this help and exit

EOF
}

function get_latest() {
    local -r name=$1
    local -r uri=$2
    local -r refs=$3

    git ls-remote --heads --tags --refs --sort="v:refname" $uri $refs | tail -n 1
}

function get_latest_commit() {
    get_latest $1 $2 $3 | awk '{print $1}'
}

function get_latest_refs() {
    get_latest $1 $2 $3 | awk '{print $2}' | awk -F'/' '{print $3}'
}

function print_repo_commit() {
    local -r repo_config=$1

    while read line; do
        # skip line
        if [[ $line =~ ^"#".*$ ]] || [[ -z "$line" ]]; then
            continue
        fi

        # read variable
        OLD_IFS="$IFS" && IFS=', '
        read name uri refs commit comment<<<$line
        IFS="$OLD_IFS"

        # Ignore if there is no commit hash
        if [ -z "$commit" ]; then
            continue
        fi

        # Skip pinned entries (comment contains "#pin")
        if [[ "$line" == *"#pin"* ]]; then
            echo "$name: skipped (pinned)"
            continue
        fi

        # For TAG_REPOS, get the latest tag within the same release series
        if [[ " $TAG_REPOS " =~ " $name " ]]; then
            if [[ " $YOCTO_TAG_REPOS " =~ " $name " ]]; then
                # yocto-<major.minor>.* (auto-migrates old codename prefix)
                version="${refs##*-}"
                search_refs="yocto-${version%.*}.*"
            else
                search_refs="${refs%%-*}-*"
            fi
        else
            search_refs="$refs"
        fi

        latest_commit="$(get_latest_commit $name $uri $search_refs)"
        latest_refs="$(get_latest_refs $name $uri $search_refs)"

        if [[ "$commit" != "$latest_commit" ]] || [[ "$refs" != "$latest_refs" ]]; then
            sed -i "/^$name,[^,]*,/s/,[^,]*,[^,]*$/,$latest_refs,$latest_commit # updated $(date +%Y-%m-%d)/" $repo_config
            echo "$name $latest_refs $latest_commit updated"
        fi

    done <$repo_config
}

if [ ! -f "$1" ]; then
    help
    exit 1
fi

print_repo_commit $1
