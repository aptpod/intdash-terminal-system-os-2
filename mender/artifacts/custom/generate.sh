#!/bin/bash -e

function help() {
    cat <<EOF
Usage: $(basename "${BASH_SOURCE[0]}") [OPTIONS]

Options:
  -d, --device-types-override           Override DEVICE_TYPES
  -h, --help                            Print this help and exit

EOF
}

SHORT=d:,h
LONG=device-types-override:,help
OPTS=$(getopt -a --options $SHORT --longoptions $LONG -- "$@")

eval set -- "$OPTS"

DEVICE_TYPES=""

while :; do
    case "$1" in
    -d | --device-types-override)
        DEVICE_TYPES="$2"
        shift 2
        ;;
    -h | --help)
        help
        exit 0
        ;;
    --)
        shift
        break
        ;;
    *)
        echo "Unexpected option: $1"
        ;;
    esac
done

for dir in $(find $(pwd) -maxdepth 1 -mindepth 1 -type d ! -name "template"); do
    cd $(readlink -f $dir)
    rm -f *.mender

    artifact="$(basename $dir)"

    echo -e "\n$artifact =============================================================="

    if [ ! -z "$(cat config.sh | grep '^DEVICE_TYPES')" ]; then
        echo "[INFO] Skip generation of artifact $artifact due to fixed DEVICE_TYPES."
        continue
    fi

    if [ -n "$DEVICE_TYPES" ]; then
        git checkout config.sh >/dev/null 2>&1
        echo "DEVICE_TYPES=(\"$DEVICE_TYPES\")" >>config.sh
    fi

    ./generate.sh

    if [ -n "$DEVICE_TYPES" ]; then
        git checkout config.sh >/dev/null 2>&1
    fi
done
