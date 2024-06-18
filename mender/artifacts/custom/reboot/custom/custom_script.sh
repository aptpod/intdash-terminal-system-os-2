#!/bin/bash

set -e

readonly STATE="$1"
readonly CUSTOM_CONTENTS_DIR="$2"
readonly CUSTOM_TMP_DIR="$3"

# reboot functions
function custom_needs_artifact_reboot() {
    # echo "Automatic" if a reboot is needed after installation, and "No" if not.
    echo "Automatic"
}

# rollback functions
function custom_supports_rollback() {
    # echo "Yes" if a rollback is supported, and "No" if not.
    echo "No"
}

case "$STATE" in
NeedsArtifactReboot)
    custom_needs_artifact_reboot
    ;;
SupportsRollback)
    custom_supports_rollback
    ;;
esac

exit 0
