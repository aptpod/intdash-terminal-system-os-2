#!/bin/bash -e

FW_PATH=$1
FW_PATH_APP0="${FW_PATH}/terminal-display_0x10000.bin"
FW_PATH_BOOTLOADER="${FW_PATH}/bootloader_qio_80m_0x1000.bin"
FW_PATH_PARTITION="${FW_PATH}/partitions_terminal-display_0x8000.bin"
FW_PATH_OTADATA="${FW_PATH}/boot_app0_0xe000.bin"
FW_PATH_VERSION="${FW_PATH}/firmware_version"

FW_VERSION_CURRENT_PATH="/run/terminal-display/firmware_version"

ESPTOOL=/usr/bin/esptool.py
DEVICE_PATH="/dev/ttyM5Stack"
MAX_RETRY=3
retry=0

new_version="$(cat $FW_PATH_VERSION)"

if [ ! -e "$DEVICE_PATH" ]; then
    echo "terminal-display is not connected"
    exit 0
fi

if [ -f "$FW_VERSION_CURRENT_PATH" ]; then
    current_version="$(cat $FW_VERSION_CURRENT_PATH)"
else
    echo "WARN: Failed to get the current version"
    current_version="unknown"
fi

if [ "$new_version" != "$current_version" ]; then
    echo "update terminal-display firmware $new_version from $current_version"

    # stop terminal-display to make serial communication exclusive.
    container_name=$(docker ps --format '{{.Names}}' | grep -E "terminal-display-client" | head -n 1)
    if [ -n "$container_name" ]; then
        docker stop $container_name
    fi

    until [ $retry -ge $MAX_RETRY ]; do
        # Flash with the same parameters as M5Burner
        python3 $ESPTOOL \
            --chip esp32 \
            --port $DEVICE_PATH \
            --baud 921600 \
            --before default_reset write_flash \
            -z \
            --flash_mode dio \
            --flash_freq 80m \
            --flash_size detect \
            0xe000 $FW_PATH_OTADATA \
            0x1000 $FW_PATH_BOOTLOADER \
            0x8000 $FW_PATH_PARTITION \
            0x10000 $FW_PATH_APP0 && break
        retry=$(($retry + 1))
        echo "update error. retry...($retry/$MAX_RETRY)"
    done
    if [ $retry -ge $MAX_RETRY ]; then
        echo "[ERROR] update terminal-display firmware failed"
        exit 1
    fi
    echo "update terminal-display firmware success"

    if [ -n "$container_name" ]; then
        docker start $container_name
    fi
else
    echo "terminal-display firmware version $new_version is already installed"
fi
