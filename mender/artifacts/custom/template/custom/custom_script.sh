#!/bin/bash

set -e

readonly STATE="$1"
readonly CUSTOM_CONTENTS_DIR="$2"
readonly CUSTOM_TMP_DIR="$3"

# - Please refer to the following document for details on state transition:
#   https://docs.mender.io/artifact-creation/create-a-custom-update-module
#
# - In case of an error, please return exit code 1

#
# === The contents of the following functions can be modified ===
#

function custom_artifact_install() {
    # Custom install process
    # Contents are located in $CUSTOM_CONTENTS_DIR
    :
}

function custom_artifact_commit() {
    :
}

function custom_artifact_failure() {
    :
}

# reboot functions
function custom_needs_artifact_reboot() {
    # echo "Automatic" if a reboot is needed after installation, and "No" if not.
    echo "No"
}

function custom_artifact_reboot() {
    :
}

function custom_artifact_verify_reboot() {
    :
}

# rollback functions
function custom_supports_rollback() {
    # echo "Yes" if a rollback is supported, and "No" if not.
    echo "No"
}

function custom_artifact_rollback() {
    :
}

function custom_artifact_rollback_reboot() {
    :
}

function custom_artifact_rollback_verify_reboot() {
    :
}

#
# === Do *NOT* change the following ===
#

case "$STATE" in
ArtifactInstall)
    custom_artifact_install
    ;;
ArtifactCommit)
    custom_artifact_commit
    ;;
ArtifactFailure)
    custom_artifact_failure
    ;;
ArtifactReboot)
    custom_artifact_reboot
    ;;
ArtifactVerifyReboot)
    custom_artifact_verify_reboot
    ;;
ArtifactRollback)
    custom_artifact_rollback
    ;;
ArtifactRollbackReboot)
    custom_artifact_rollback_reboot
    ;;
ArtifactRollbackVerifyReboot)
    custom_artifact_rollback_verify_reboot
    ;;
NeedsArtifactReboot)
    custom_needs_artifact_reboot
    ;;
SupportsRollback)
    custom_supports_rollback
    ;;
esac

exit 0
