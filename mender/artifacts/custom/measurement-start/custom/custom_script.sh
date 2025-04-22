#!/bin/bash

set -e

readonly STATE="$1"
readonly CUSTOM_CONTENTS_DIR="$2"
readonly CUSTOM_TMP_DIR="$3"

function custom_artifact_install() {
    # Custom install process
    # Contents are located in $CUSTOM_CONTENTS_DIR
    stdout=$(mktemp) || { echo "failed to create temp file" >&2; exit 1; }
    stderr=$(mktemp) || { echo "failed to create temp file" >&2; exit 1; }
    set +e
    curl --fail-with-body -sSL -X GET http://localhost:8081/api/agent/streamer/checklist >"$stdout" 2>"$stderr"
    exit_code=$?
    set -e
    if [ $exit_code -ne 0 ]; then
        cat "$stdout"
        cat "$stderr" >&2
        rm "$stdout" "$stderr"
        exit $exit_code
    fi
    if [ "$(jq ".ready_to_run // false" "$stdout")" != "true" ]; then
        cat "$stdout"
        echo "intdash Edge Agent 2 is not configured for data transmission" >&2
        rm "$stdout" "$stderr" 
        exit 1
    fi
    rm "$stdout" "$stderr" 

   curl --fail-with-body -sSL -X POST http://localhost:8081/api/docker/composes/measurement/start
}

# reboot functions
function custom_needs_artifact_reboot() {
    # echo "Automatic" if a reboot is needed after installation, and "No" if not.
    echo "No"
}

# rollback functions
function custom_supports_rollback() {
    # echo "Yes" if a rollback is supported, and "No" if not.
    echo "No"
}

case "$STATE" in
ArtifactInstall)
    custom_artifact_install
    ;;
NeedsArtifactReboot)
    custom_needs_artifact_reboot
    ;;
SupportsRollback)
    custom_supports_rollback
    ;;
esac

exit 0
