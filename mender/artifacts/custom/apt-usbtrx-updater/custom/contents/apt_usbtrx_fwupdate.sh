#!/bin/bash -e

APTUSB_DIR=/dev/apt-usb/by-id/
BINDIR=/usr/bin
FW_PATH=$1

declare -A FW_NAMES=(
    ["EP1-CH02A"]="EP1-CH02A"
    ["EP1-AG08A"]="EP1-AG08A"
)

get_version_from_filename() {
    local f=$1
    echo $f | grep -o -E "[0-9]+\.[0-9]+(\.[0-9]+)?"
}

get_latest_firmware_path() {
    local product=$1
    local path=$FW_PATH
    ls ${path%/}/${product}/${FW_NAMES[${product}]}*.bin | sort -r | head -n 1
}

for device_path in /dev/aptUSB*; do
    if [ ! -e "$device_path" ]; then
        continue
    fi

    # Get by sysfs
    device_name="$(basename $device_path)"
    version="$(cat /sys/class/usbmisc/$device_name/device/firmware_version)"
    channel="$(cat /sys/class/usbmisc/$device_name/device/ch)"

    # Update is only available on channel 0
    if [ $channel -ne 0 ]; then
        continue
    fi

    # Get by udevadm
    product="$(udevadm info --query=all --name=$device_path | grep 'ID_MODEL=' | awk -F= '{print $2}')"
    serial="$(udevadm info --query=all --name=$device_path | grep 'ID_SERIAL_SHORT=' | awk -F= '{print $2}')"

    if [ -z "${FW_NAMES[${product}]}" ]; then
        echo "Warning: $product is not supported"
        continue
    fi

    fwfile=$(get_latest_firmware_path $product)
    fw_version=$(get_version_from_filename $fwfile)

    if [ "$version" != "$fw_version" ]; then
        echo "update $product (S/N: $serial) firmware version $fw_version from $version"
        $BINDIR/apt_usbtrx_fwupdate.py --firmware $fwfile $device_path
        if [ $? != 0 ]; then
            exit 1
        fi
    else
        echo "firmware version $fw_version is already installed on $product (S/N: $serial) "
    fi
done
