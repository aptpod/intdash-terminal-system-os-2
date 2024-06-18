#!/bin/bash -e

readonly THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
readonly TS_CONFIGD_DIR_DEFAULT="configs"
readonly TS_CONFIGS_DIR="${TS_CONFIGS_DIR:=$TS_CONFIGD_DIR_DEFAULT}"
readonly VERSION_CONF="$TS_CONFIGS_DIR/version.conf"
readonly CONFIGS_DIR="$TS_CONFIGS_DIR/$(grep 'TS_CONFIGS_VERSION' $VERSION_CONF | cut -d'=' -f2)"
readonly DOCKER_DIR="docker"

function help() {
    cat <<EOF
Usage: $(basename "${BASH_SOURCE[0]}") --image-dir ./docker/<image> [--target <TARGET> | --tag <image_name:tag> | --push]

Options:
  --image-dir            Image Directory (./docker/<image>)
  -t, --target           Build Target (Required only for device-connector-intdash)
  --tag                  Image Tag
  --push                 Push Image
  -h, --help             Print this help and exit

Optional Variables:
  TS_CONFIGS_DIR         Configs Directory (default: "$(dirname $THIS_DIR)/$TS_CONFIGD_DIR_DEFAULT")

Target:
$(find $CONFIGS_DIR -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | grep -vE "^all$|^template$" | sed 's/^/  /' | sort)

EOF
}

function setup_environments_config() {
    local -r config="$1"

    while read line; do
        # skip line
        if [[ $line =~ ^"#".*$ ]] || [[ -z "$line" ]]; then
            continue
        fi
        key=${line%%=*}
        value=${line#*=}
        eval value_expanded="$value"

        export "$key"="$value_expanded"
    done <$config
}

function setup_environments() {
    setup_environments_config "$VERSION_CONF"
    setup_environments_config "$CONFIGS_DIR/all/environments.conf"

    if [ "$IMAGE_NAME" == "device-connector-intdash" ]; then
        setup_environments_config "$CONFIGS_DIR/$TARGET/environments.conf"
    fi
}

function download_package() {
    local -r package=$1
    local -r uri=$2
    local -r filename=$3
    local -r header="$4"

    if [ -n "$filename" ]; then
        output="$IMAGE_DIR/$filename"
    else
        output="$IMAGE_DIR/$(basename $uri)"
    fi

    echo "download $package $DEB_ARCH"
    curl -fsSL -o "$output" -H "$header" $uri
}

function download_packages() {
    local -r packages_config="$1"

    rm -rf "$IMAGE_DIR"/*.deb

    while read line; do
        # skip line
        if [[ $line =~ ^"#".*$ ]] || [[ -z "$line" ]]; then
            continue
        fi

        # read variable
        OLD_IFS="$IFS" && IFS=' '
        read image package architectures uri filename header <<<$line
        IFS="$OLD_IFS"

        if [ "$image" != "$IMAGE_NAME" ]; then
            continue
        fi

        for arch in $(echo $architectures | tr ',' ' '); do
            # variable expansion
            export DEB_ARCH=$arch
            eval "export uri_expanted=$uri"
            eval "export filename_expanded=$filename"

            download_package $package $uri_expanted $filename_expanded "$header"
        done

    done <$packages_config
}

function setup_buildx() {
    # parepare buildx builder instance
    if ! docker buildx ls | grep -q 'mybuild' >/dev/null; then
        docker buildx create --use --name mybuild >/dev/null
    fi
}

function build_docker_image() {
    local -r image_dir=$1

    (
        cd "$image_dir"
        source .env

        if [ "$IMAGE_NAME" == "device-connector-intdash" ]; then
            BUILD_ARGS+=" --build-arg TS_BASE_IMAGE_DEVICE_CONNECTOR=${TS_BASE_IMAGE_DEVICE_CONNECTOR}"
            BUILD_ARGS+=" --build-arg TS_INSTALL_PACKAGES_DEVICE_CONNECTOR=${TS_INSTALL_PACKAGES_DEVICE_CONNECTOR}"
        fi

        if [ "$IMAGE_NAME" != "builder" ]; then
            TARGET_DESCRIPTION="for $TARGET $IMAGE_PLATFORM"
        fi
        echo "Build docker image \"$IMAGE_NAME\" $TARGET_DESCRIPTION"

        docker buildx build $BUILD_ARGS --platform ${IMAGE_PLATFORM} .

        echo "Successfully built docker image \"$IMAGE_NAME\" $TARGET_DESCRIPTION"
        echo ""
    )
}

SHORT=t:,h
LONG=target:,image-dir:,tag:,push,help
OPTS=$(getopt -a --options $SHORT --longoptions $LONG -- "$@")

eval set -- "$OPTS"

PUSH_IMAGES=false
BUILD_ARGS=""

while :; do
    case "$1" in
    -t | --target)
        TARGET="$2"
        shift 2
        ;;
    --image-dir)
        IMAGE_DIR="$2"
        shift 2
        ;;
    --tag)
        IMAGE_TAG="$2"
        BUILD_ARGS+=" --tag $IMAGE_TAG"
        shift 2
        ;;
    --push)
        PUSH_IMAGES=true
        BUILD_ARGS+=" --push"
        shift 1
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

if [ -z "$IMAGE_DIR" ]; then
    help
    exit 1
fi

if [ ! -d "$IMAGE_DIR" ]; then
    echo "ERROR: Image directory ($IMAGE_DIR) is not found."
    exit 1
else
    export IMAGE_NAME="$(basename $IMAGE_DIR)"
fi

if [ "$IMAGE_NAME" == "device-connector-intdash" ] && [ ! -d "$CONFIGS_DIR/$TARGET" ]; then
    echo "ERROR: Target config directory ($CONFIGS_DIR/$TARGET) is not found."
    exit 1
fi

if [ "$PUSH_IMAGES" = true ] && [ -z "$IMAGE_TAG" ]; then
    echo "ERROR: Set --tag option for push."
    exit 1
fi

setup_environments
setup_buildx
download_packages "$CONFIGS_DIR/all/external_packages.conf"
build_docker_image $IMAGE_DIR
