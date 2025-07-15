#!/bin/bash -e

TS_CONFIGS_DIR=${TS_CONFIGS_DIR:=../../../../configs}
if [ -e "$TS_CONFIGS_DIR/version.conf" ]; then
    source $TS_CONFIGS_DIR/version.conf
fi
source config.sh

# DEVICE_TYPES is set based on the configs directory
if [ -z "$DEVICE_TYPES" ] && [ -e "$TS_CONFIGS_DIR/version.conf" ]; then
    readonly DEVICE_TYPES=($(find "$TS_CONFIGS_DIR/$TS_CONFIGS_VERSION" -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | grep -vE "^all$|^template$"))
fi
readonly CUSTOM_DIR="custom"
readonly CUSTOM_SCRIPT_PATH="${CUSTOM_DIR}/custom_script.sh"
readonly CONTENTS_DIR="${CUSTOM_DIR}/contents"
readonly OUTPUT_DIR=${1:-"."}
readonly METADATA_JSON="metadata.json"
readonly CUSTOM_ARTIFACT_GEN="$(readlink -f ../custom-artifact-gen)"

function init_custom_dir() {
    mkdir -p ${CONTENTS_DIR}
}

function generate_update_module() {
    local device_type_args=""
    for d in "${DEVICE_TYPES[@]}"; do
        device_type_args="${device_type_args} -t ${d}"
    done

    local artifact_version_args=""
    if [ -n "${ARTIFACT_VERSION}" ]; then
        artifact_version_args="-v ${ARTIFACT_VERSION}"
    fi

    local mender_artifact_args="--"
    if [ -f "${METADATA_JSON}" ]; then
        mender_artifact_args="${mender_artifact_args} --meta-data ${METADATA_JSON}"
    fi

    local software_filesystem="rootfs-image"
    if [ -n "${SOFTWARE_FILESYSTEM}" ]; then
        software_filesystem="${SOFTWARE_FILESYSTEM}"
    fi

    ${CUSTOM_ARTIFACT_GEN} \
        -n ${ARTIFACT_NAME} \
        ${device_type_args} \
        -s ${CUSTOM_SCRIPT_PATH} \
        ${artifact_version_args} \
        -c ${CONTENTS_DIR} \
        -f ${software_filesystem} \
        -o ${OUTPUT_DIR} \
        ${mender_artifact_args}
}

init_custom_dir
generate_update_module
