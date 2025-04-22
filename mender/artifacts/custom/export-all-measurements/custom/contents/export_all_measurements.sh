#!/usr/bin/env bash
export LC_ALL=C
set -e

NAME="export-all-measurements"

old_ifs=$IFS
IFS='
'

parts=$(lsblk -J | jq -rc '.blockdevices[] | select(.rm == true and .ro == false) | .children // [.] | .[].name')
for part in $parts; do
  mountpoints=$(lsblk -J "/dev/$part" | jq -rc '.blockdevices[].mountpoints[] // empty')

  mountpoint=
  if [ -z "$mountpoints" ]; then
    mountpoint="/mnt/$RANDOM"
    mkdir -p "$mountpoint"
    mount "/dev/$part" "$mountpoint"
    mountpoints="$mountpoint"
  fi

  exported=
  for dir in $mountpoints; do
    if [ -e "$dir/$NAME" ]; then
      filename="exported-measurements-$(date +'%Y%m%d%H%M%S').zip"
      curl --fail-with-body -sSL -X GET -o "$dir/$filename" http://localhost:8081/api/agent/measurements/-/download
      exported="Agent 2 measurements were exported as $filename to /dev/$part"
      break
    fi
  done

  if [ -n "$mountpoint" ]; then
    umount "$mountpoint"
    rm -rf "$mountpoint"
  fi

  if [ -n "$exported" ]; then
    echo "$exported"
    break
  fi
done

IFS=$old_ifs

if [ -z "$parts" ]; then
  echo "Error: No removable storage device found. Please connect one and try again."
  exit 1
fi

if [ -z "$exported" ]; then
  echo "Error: Export failed. Please check the '$NAME' file in the root of the removable storage device."
  exit 1
fi

exit 0