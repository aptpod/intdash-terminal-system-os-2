#!/bin/bash -e

POWERMANAGE_BIN=/usr/bin/edgeplant-l4t/edgeplant_powermanage
FW_PATH=$1

# Lock is used by device-invenotry tool for exclusive handling
LOCK_DIR=/var/lock
LOCK_FILE="edgeplant_powermanage.lock"
LOCK_PATH="$LOCK_DIR/$LOCK_FILE"
LOCK_TIMEOUT=10

declare -A FW_NAMES=(
    ["edgeplant-t1"]="ET1-128NJA"
)

get_version() {
    $POWERMANAGE_BIN version | sed -e 's/version: //g'
}

get_version_from_filename() {
    local f=$1
    echo $f | grep -o -E "[0-9]+\.[0-9]+(\.[0-9]+)?"
}

get_latest_firmware_path() {
    local product=$1
    local path=$FW_PATH
    ls ${path%/}/${FW_NAMES[${product}]}*.bin | sort -r | head -n 1
}

product="edgeplant-t1"
fwfile=$(get_latest_firmware_path $product)
version="$(get_version)"
fw_version=$(get_version_from_filename $fwfile)

if [ "$version" != "$fw_version" ]; then
    echo "update powermanage firmware version $fw_version from $version"
    return_code=0
    flock --timeout $LOCK_TIMEOUT $LOCK_PATH -c "yes N | $POWERMANAGE_BIN update -f:$fwfile" || return_code=$?
    if [ $return_code -ne 0 ]; then
        echo "ERRPR: powermanage firmware update failed"
        exit 1
    fi
else
    echo "powermanage firmware version $fw_version is already installed"
fi
