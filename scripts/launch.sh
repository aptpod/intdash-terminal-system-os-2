#!/bin/bash -e

readonly THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
readonly TS_CONFIGD_DIR_DEFAULT="configs"
readonly TS_CONFIGS_DIR="${TS_CONFIGS_DIR:=$TS_CONFIGD_DIR_DEFAULT}"
readonly VERSION_CONF="$TS_CONFIGS_DIR/version.conf"
readonly CONFIGS_DIR="$TS_CONFIGS_DIR/$(grep 'TS_CONFIGS_VERSION' $VERSION_CONF | cut -d'=' -f2)"

function help() {
    cat <<EOF
Usage: $(basename "${BASH_SOURCE[0]}") [-h]

Options:
  -h, --help      Print this help and exit

Optional Variables:
  DL_DIR            Download Directory (default: "$(dirname $THIS_DIR)/downloads")
  SSTATE_CACHE_DIR  Sahred state cache Directory (default: "$(dirname $THIS_DIR)/sstate-cache")
  TS_CONFIGS_DIR    Configs Directory (default: "$(dirname $THIS_DIR)/$TS_CONFIGD_DIR_DEFAULT")

EOF
}

SHORT=h
LONG=help
OPTS=$(getopt -a --options $SHORT --longoptions $LONG -- "$@")

eval set -- "$OPTS"

while :; do
    case "$1" in
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

if [ ! -e "$CONFIGS_DIR/all/environments.conf" ]; then
    echo "ERROR: configs-dir ($CONFIGS_DIR/all/environments.conf) is not found."
    exit 1
fi

source $VERSION_CONF
source $CONFIGS_DIR/all/environments.conf
IMAGE="$TS_IMAGE_BASE_URI_BUILDER/$TS_IMAGE_NAME_BUILDER:$TS_IMAGE_TAG_BUILDER"

USER=root
CMD=${@:-bash}
TIMEZONE="Asia/Tokyo"

# mount opts
MOUNT_OPTS="--mount type=bind,source=$THIS_DIR/../,target=/home/builder/work"
if [ -n "$DL_DIR" ]; then
    echo "INFO: Applying bind mount for the downloads directory \"$DL_DIR\" to \"/home/builder/work/downloads\"."
    MOUNT_OPTS="$MOUNT_OPTS --mount type=bind,source=$DL_DIR,target=/home/builder/work/downloads"
fi
if [ -n "$SSTATE_CACHE_DIR" ]; then
    echo "INFO: Applying bind mount for the sstate-cache directory \"$SSTATE_CACHE_DIR\" to \"/home/builder/work/sstate-cache\"."
    MOUNT_OPTS="$MOUNT_OPTS --mount type=bind,source=$SSTATE_CACHE_DIR,target=/home/builder/work/sstate-cache"
fi
if [ "$(realpath "$TS_CONFIGS_DIR")" != "$(realpath "$TS_CONFIGD_DIR_DEFAULT")" ]; then
    echo "INFO: Applying bind mount for the configs directory \"$TS_CONFIGS_DIR\" to \"/home/builder/work/$TS_CONFIGD_DIR_DEFAULT\"."
    MOUNT_OPTS="$MOUNT_OPTS --mount type=bind,source=$TS_CONFIGS_DIR,target=/home/builder/work/$TS_CONFIGD_DIR_DEFAULT"
fi

# launch
docker pull $IMAGE
docker run --rm -it \
    --volume $SSH_AUTH_SOCK:/ssh-agent --env SSH_AUTH_SOCK=/ssh-agent \
    $MOUNT_OPTS \
    --shm-size=1gb \
    --env=TERM=xterm-256color \
    --net=host \
    --user "$USER" \
    --privileged \
    --env TZ="$TIMEZONE" \
    $IMAGE \
    $CMD
