#!/bin/bash -e

BINDIR=/usr/bin

for device_path in /dev/aptUSB*; do
    if [ ! -e "$device_path" ]; then
        continue
    fi

    # Check product
    product="$(udevadm info --query=all --name=$device_path | grep 'ID_MODEL=' | awk -F= '{print $2}')"
    if [ "${product}" != "EP1-CF02A" ]; then
        continue
    fi

    # Check channel
    device_name="$(basename $device_path)"
    channel="$(cat /sys/class/usbmisc/$device_name/device/ch)"
    if [ $channel -ne 0 ]; then
        continue
    fi

    serial="$(udevadm info --query=all --name=$device_path | grep 'ID_SERIAL_SHORT=' | awk -F= '{print $2}')"

    # Format SD
    $BINDIR/ep1_cf02a_init_store_data_media -f $device_path
    if [ $? != 0 ]; then
        echo "Failed to format SD card on $product (S/N: $serial)"
        exit 1
    fi
    echo "SD card formatted successfully on $product (S/N: $serial)"
done
