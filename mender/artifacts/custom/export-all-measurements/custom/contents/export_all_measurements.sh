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
  export_failed=
  for dir in $mountpoints; do
    if [ -e "$dir/$NAME" ]; then
      filename="exported-measurements-$(date +'%Y%m%d%H%M%S').zip"

      query_params=""
      if grep -qE '^clean=true$' "$dir/$NAME"; then
        query_params="?clean=true"
      fi

      curl_exit_code=0
      curl --fail-with-body -sSL -X GET -o "$dir/$filename" "http://localhost:8081/api/agent/measurements/-/download$query_params" || curl_exit_code=$?

      if [ $curl_exit_code -ne 0 ]; then
        if [ $curl_exit_code -eq 23 ]; then
          avail=$(df --output=avail -k "$dir" 2>/dev/null | tail -1)
          export_failed="Error: Export failed. The USB storage ($dir) may be full. Available space: ${avail:-unknown} KB"
        else
          export_failed="Error: Export failed."
        fi
        rm -f "$dir/$filename"
        break
      fi

      exported="Agent 2 measurements were exported as $filename to /dev/$part"
      break
    fi
  done

  if [ -n "$mountpoint" ]; then
    umount "$mountpoint"
    rm -rf "$mountpoint"
  fi

  if [ -n "$export_failed" ]; then
    echo "$export_failed"
    exit 1
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