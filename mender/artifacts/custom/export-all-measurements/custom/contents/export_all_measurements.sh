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
      curl -fsSL -X GET -o "$dir/$filename" http://localhost:8081/api/agent/measurements/-/download
      exported="Agent 2 measurements were exported as $filename to /dev/$part"
    fi
    break
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

exit 0