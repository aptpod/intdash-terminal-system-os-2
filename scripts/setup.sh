#!/bin/bash -e

readonly THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
readonly TS_CONFIGD_DIR_DEFAULT="configs"
readonly TS_CONFIGS_DIR="${TS_CONFIGS_DIR:=$TS_CONFIGD_DIR_DEFAULT}"
readonly VERSION_CONF="$TS_CONFIGS_DIR/version.conf"
readonly CONFIGS_DIR="$TS_CONFIGS_DIR/$(grep 'TS_CONFIGS_VERSION' $VERSION_CONF | cut -d'=' -f2)"
readonly POKY_DIR="poky"
readonly MENDER_ARTIFACTS_CUSTOM_DIR="mender/artifacts/custom"
readonly TMPFILE_GIT=/tmp/setup_sh_git_stderr_tmp
readonly EXTERNAL_OUT_DIR="$(readlink -f "${THIS_DIR}"/../resources)"
readonly BUILD_ENVS=(
)
readonly BUILD_OPT_ENVS=(
    "TS_MENDER_TENANT_TOKEN"
    "TS_MENDER_EMAIL"
    "TS_MENDER_PASS"
    "TS_AWS_CREDS_DEF_ACCESS_KEY_ID"
    "TS_AWS_CREDS_DEF_SECRET_ACCESS_KEY"
    "TS_AWS_ECR_BASE_URI"
    "NVDCVE_API_KEY"
    "TS_CVE_CHECK_EXIT"
)

function help() {
    cat <<EOF
Usage: $(basename "${BASH_SOURCE[0]}") [OPTIONS]

Options:
  -t, --target                          Build Target
  -e, --env-override                    Override environment variables in the configuration file with local environment variables.
  -h, --help                            Print this help and exit

Target:
$(find $CONFIGS_DIR -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | grep -vE "^all$|^template$" | sed 's/^/  /' | sort)

Optional Variables:
  TS_CONFIGS_DIR                        Configs Directory (default: "$(dirname $THIS_DIR)/$TS_CONFIGD_DIR_DEFAULT")

  Mender credentials:
    TS_MENDER_TENANT_TOKEN              Mender tenant/organization token
    TS_MENDER_EMAIL                     Mender Email
    TS_MENDER_PASS                      Mender Password

  ECR credentials:
    TS_AWS_CREDS_DEF_ACCESS_KEY_ID      Access key id
    TS_AWS_CREDS_DEF_SECRET_ACCESS_KEY  Secret access key
    TS_AWS_ECR_BASE_URI                 ECR base URI

EOF
}

function check_environments() {
    for env in "${BUILD_ENVS[@]}"; do
        if [ -z "$(eval echo '$'$env)" ]; then
            help
            echo ""
            echo "ERROR: Set variables \"$env\""
            exit 1
        fi
    done
}

function checkout_repository() {
    local -r name=$1
    local -r uri=$2
    local -r branch=$3
    local -r commit=$4

    echo "checkout $name $branch $commit"

    if [ "$name" == "$POKY_DIR" ]; then
        workdir=.
    else
        workdir="./$POKY_DIR"
    fi

    (
        # clone
        cd $workdir
        if [ -d "$name" ]; then
            cd $name
            if [ ! -d ".git" ]; then
                git init --quiet
                git remote add origin $uri
            fi
            git fetch --depth 1 origin $branch >$TMPFILE_GIT 2>&1 || (cat $TMPFILE_GIT && false)
            git checkout --quiet FETCH_HEAD
        else
            git clone --depth 1 -b $branch $uri $name >$TMPFILE_GIT 2>&1 || (cat $TMPFILE_GIT && false)
        fi
    )

    (
        # checkout
        if [ -n "$commit" ]; then
            cd $workdir/$name
            git reset --hard HEAD >/dev/null 2>&1
            git checkout $commit >/dev/null 2>&1 && true
            if [ $? -ne 0 ]; then
                git fetch --unshallow >$TMPFILE_GIT 2>&1 || (cat $TMPFILE_GIT && false)
                git checkout $commit >$TMPFILE_GIT 2>&1 || (cat $TMPFILE_GIT && false)
            fi
        fi
    )
}

function setup_repository() {
    local -r repo_config="$1"

    while read line; do
        # skip line
        if [[ $line =~ ^"#".*$ ]] || [[ -z "$line" ]]; then
            continue
        fi

        # read variable
        OLD_IFS="$IFS" && IFS=,
        read name uri branch commit <<<$line
        IFS="$OLD_IFS"

        checkout_repository $name $uri $branch $commit
    done <$repo_config
}

function initialize_build_dir() {
    (
        cd "./$POKY_DIR"
        . oe-init-build-env build >/dev/null 2>&1
    )
}

function copy_configs() {
    local -r local_config="$CONFIGS_DIR/all/local.conf"
    local -r local_config_inc="$CONFIGS_DIR/$TARGET/local.conf.inc"
    local -r bblayers_config="$CONFIGS_DIR/all/bblayers.conf"
    local -r bblayers_config_inc="$CONFIGS_DIR/$TARGET/bblayers.conf.inc"
    local -r all_cve_config="$CONFIGS_DIR/all/cve.conf"
    local -r target_cve_config="$CONFIGS_DIR/$TARGET/cve.conf"

    # cve.conf is kept private and may be absent on the public mirror.
    cat $local_config $local_config_inc > "$POKY_DIR/build/conf/local.conf"
    if [ -f "$all_cve_config" ]; then
        cat "$all_cve_config" >> "$POKY_DIR/build/conf/local.conf"
    fi
    if [ -f "$target_cve_config" ]; then
        cat "$target_cve_config" >> "$POKY_DIR/build/conf/local.conf"
    fi
    cat $bblayers_config $bblayers_config_inc > "$POKY_DIR/build/conf/bblayers.conf"
}

function initialize_external_out_dir() {
    rm -rf "$EXTERNAL_OUT_DIR"
    mkdir -p ${EXTERNAL_OUT_DIR}
}

function download_external_source() {
    local -r name=$1
    local -r uri=$2
    local -r filename=$3
    local -r header="$4"

    if [ -n "$filename" ]; then
        output="$EXTERNAL_OUT_DIR/$filename"
    else
        output="$EXTERNAL_OUT_DIR/$(basename $uri)"
    fi

    if [[ "$name" == "mender-binary-delta" ]]; then
        if [[ ! "$TS_FEATURES" == *"mender-binary-delta"* ]]; then
            echo "INFO: TS_FEATURES mender-binary-delta is disabled. mender-binary-delta will not be installed."
            return
        fi

        echo "download $name"
        if [ -n "$TS_MENDER_EMAIL" ] && [ -n "$TS_MENDER_PASS" ]; then
            if ! curl -fsSL -u $TS_MENDER_EMAIL:$TS_MENDER_PASS -o "$output" $uri; then
                echo "ERROR: Failed to download mender-binary-delta. Please check your Mender account credentials."
                exit 1
            fi
        else
            echo "ERROR: Failed to download mender-binary-delta. Please set variables \"TS_MENDER_EMAIL\" and \"TS_MENDER_PASS\", or remove mender-binary-delta from \"TS_FEATURES\"."
            exit 1
        fi
    else
        echo "download $name"
        curl -fsSL -o "$output" -H "$header" $uri
    fi
}

# Sets RESOLVED_HEADER instead of echoing the result: a command substitution would
# run the exit below in a subshell and let the caller continue.
function resolve_header() {
    local header="$1"
    local -r context="$2"

    RESOLVED_HEADER="$header"

    if [[ "$header" != *'$'* ]] && [[ "$header" != *'`'* ]]; then
        return
    fi

    local -r envs=$(echo "$header" | grep -oE '\$\{[A-Za-z_][A-Za-z0-9_]*\}' | tr -d '${}')

    local residue="$header"
    local env
    for env in $envs; do
        residue=${residue//\$\{$env\}/}
    done
    if [[ "$residue" == *'$'* ]] || [[ "$residue" == *'`'* ]]; then
        echo "ERROR: Unsupported notation in the header for \"$context\". Use \${NAME}."
        exit 1
    fi

    for env in $envs; do
        if [ -z "${!env}" ]; then
            echo "ERROR: Set variables \"$env\" (required by \"$context\")"
            exit 1
        fi
        header=${header//\$\{$env\}/${!env}}
    done

    RESOLVED_HEADER="$header"
}

function download_external_sources() {
    local -r external_config="$1"

    while read line; do
        # skip line
        if [[ $line =~ ^"#".*$ ]] || [[ -z "$line" ]]; then
            continue
        fi

        # read variable
        OLD_IFS="$IFS" && IFS=,
        read name uri filename header <<<$line
        IFS="$OLD_IFS"

        resolve_header "$header" "$name"

        # variable expansion
        eval "export uri=$uri"
        eval "export filename=$filename"

        download_external_source $name $uri $filename "$RESOLVED_HEADER"
    done <$external_config
}

function docker_login_aws_ecr() {
    if [ -n "${TS_AWS_ECR_BASE_URI}" ] &&
        [ -n "${TS_AWS_CREDS_DEF_ACCESS_KEY_ID}" ] &&
        [ -n "${TS_AWS_CREDS_DEF_SECRET_ACCESS_KEY}" ] &&
        [ -n "${TS_AWS_CONFIG_DEF_REGION}" ]; then

        export AWS_SECRET_ACCESS_KEY=${TS_AWS_CREDS_DEF_SECRET_ACCESS_KEY}
        export AWS_ACCESS_KEY_ID=${TS_AWS_CREDS_DEF_ACCESS_KEY_ID}
        export AWS_DEFAULT_REGION=${TS_AWS_CONFIG_DEF_REGION}
        aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | docker login --username AWS --password-stdin ${TS_AWS_ECR_BASE_URI} >/dev/null 2>&1
    fi
}

function download_external_docker_images() {
    mkdir -p "${EXTERNAL_OUT_DIR}"

    local -r external_docker_images_config="$1"
    local src_uri

    docker_login_aws_ecr

    while read -r line; do
        # skip line
        if [[ $line =~ ^"#".*$ ]] || [[ -z "$line" ]]; then
            continue
        fi

        eval "image=${line}"
        tag="${image##*:}"
        repo="${image%:*}"
        if [[ "${repo}" =~ / ]]; then
            name="$(echo ${repo#*/} | sed 's/\//_/g')"
        else
            name="${repo}"
        fi

        echo "download preinstall docker image $image for ${TS_TARGET_GOOS} ${TS_TARGET_GOARCH}"
        platform="${TS_TARGET_GOOS}/${TS_TARGET_GOARCH}"

        # docker pull
        if ! docker pull --platform ${platform} -q ${image}; then
            echo "pull error ${image}"
            exit 1
        fi

        # docker save
        # NOTE: set the extension to docker-archive-load, to avoid unpack
        archive="docker-preinstall-image_${name}_${tag}.tar.gz.docker-archive-load"
        if [ -f "${EXTERNAL_OUT_DIR}/${archive}" ]; then
            rm "${EXTERNAL_OUT_DIR}/${archive}"
        fi

        docker save --platform ${platform} ${image} | gzip --rsyncable >${EXTERNAL_OUT_DIR}/${archive}
        if [ ! -f "${EXTERNAL_OUT_DIR}/${archive}" ]; then
            echo "Error saving ${archive}"
            exit 1
        fi

        # remove untagged image
        for img in $(docker images | /bin/grep "${repo}" | grep '<none>' | awk '{print $3}'); do
            docker rmi ${img}
        done
    done <$external_docker_images_config
}

function export_archived_docker_images() {
    local src_uri=$(find "${EXTERNAL_OUT_DIR}" -name "*.tar.gz.docker-archive-load" -exec echo "file://{}" \; | tr '\n' ' ')

    # export TS_SRC_URI_DOCKER_ARCHIVE_LOAD for bitbake docker-archive-load recipe
    echo "export TS_SRC_URI_DOCKER_ARCHIVE_LOAD=\"${src_uri}\"" >>"$POKY_DIR/oe-init-build-env"
    echo "export BB_ENV_PASSTHROUGH_ADDITIONS=\"\$BB_ENV_PASSTHROUGH_ADDITIONS TS_SRC_URI_DOCKER_ARCHIVE_LOAD\"" >>"$POKY_DIR/oe-init-build-env"
}

function generate_mender_artifacts() {
    echo "generate mender artifacts"

    (
        cd "./$MENDER_ARTIFACTS_CUSTOM_DIR"

        # generate artifacts
        if ! ./generate.sh > /dev/null 2>&1; then
            echo "ERROR: Failed to generate mender artifacts."
            exit 1
        fi

        # copy operation artifacts to external out dir
        for artifact in $(find . -maxdepth 2 -mindepth 2 -type f -name "*.mender"); do
            custom_artifact_type="$(mender-artifact read "$artifact" 2>/dev/null | grep -P -o '"custom_artifact_type":\s*"\K[^"]*')"
            if [ "$custom_artifact_type" = "operation" ]; then
                # Remove version from filename
                basename=$(basename "$artifact")
                new_name=$(echo "$basename" | sed -E 's/_[^_]*\.mender$/.mender/')
                cp "$artifact" "$EXTERNAL_OUT_DIR/$new_name"
            fi
        done
    )

    # export TS_SRC_URI_MENDER_OPERATION_ARTIFACTS for bitbake terminal-system-cored recipe
    local src_uri=$(find "${EXTERNAL_OUT_DIR}" -name "*.mender" -exec echo "file://{}" \; | tr '\n' ' ')
    echo "export TS_SRC_URI_MENDER_OPERATION_ARTIFACTS=\"${src_uri}\"" >>"$POKY_DIR/oe-init-build-env"
    echo "export BB_ENV_PASSTHROUGH_ADDITIONS=\"\$BB_ENV_PASSTHROUGH_ADDITIONS TS_SRC_URI_MENDER_OPERATION_ARTIFACTS\"" >>"$POKY_DIR/oe-init-build-env"
}

function setup_external() {
    initialize_external_out_dir

    download_external_sources "$CONFIGS_DIR/all/external_sources.conf"
    download_external_sources "$CONFIGS_DIR/$TARGET/external_sources.conf"

    download_external_docker_images "$CONFIGS_DIR/all/external_docker_images.conf"
    export_archived_docker_images

    generate_mender_artifacts
}

function show_layers() {
    (
        cd "./$POKY_DIR"
        source oe-init-build-env build >/dev/null 2>&1
        bitbake-layers show-layers
    )
}

function setup_environments_config() {
    local -r config="$1"

    while read line; do
        # skip line
        if [[ $line =~ ^"#".*$ ]] || [[ -z "$line" ]]; then
            continue
        fi
        key=${line%%=*}

        # Check local environment variables
        eval local_env_value='$'"${key}"
        if [ "${ENV_OVERRIDE}" = true ] && [ -n "$local_env_value" ]; then
            # Only single quotes to prevent multiple escapes when executing multiple times
            value="'${local_env_value}'"
            value_expanded="${local_env_value}"
        else
            value=${line#*=}
            eval value_expanded="$value"
        fi

        export "$key"="$value_expanded"
        # export for bitbake
        if [[ $value =~ ^\'.*\'$ ]]; then
            echo "export $key='$value_expanded'" >>"$POKY_DIR/oe-init-build-env"
        else
            echo "export $key=\"$value_expanded\"" >>"$POKY_DIR/oe-init-build-env"
        fi
        echo "export BB_ENV_PASSTHROUGH_ADDITIONS=\"\$BB_ENV_PASSTHROUGH_ADDITIONS $key\"" >>"$POKY_DIR/oe-init-build-env"
    done <$config
}

function setup_environments() {
    # credential variables
    for env in "${BUILD_ENVS[@]}"; do
        if [ -n "$(eval echo '$'$env)" ]; then
            echo "export BB_ENV_PASSTHROUGH_ADDITIONS=\"\$BB_ENV_PASSTHROUGH_ADDITIONS $env\"" >>"$POKY_DIR/oe-init-build-env"
        fi
    done

    for env in "${BUILD_OPT_ENVS[@]}"; do
        if [ -n "$(eval echo '$'$env)" ]; then
            echo "export BB_ENV_PASSTHROUGH_ADDITIONS=\"\$BB_ENV_PASSTHROUGH_ADDITIONS $env\"" >>"$POKY_DIR/oe-init-build-env"
        fi
    done

    # auto set variables
    export TS_AWS_CONFIG_DEF_REGION=$(echo ${TS_AWS_ECR_BASE_URI} | sed 's/.*\.\(.*\)\.amazonaws\.com/\1/')
    echo "export TS_AWS_CONFIG_DEF_REGION=${TS_AWS_CONFIG_DEF_REGION}" >>"$POKY_DIR/oe-init-build-env"
    echo "export BB_ENV_PASSTHROUGH_ADDITIONS=\"\$BB_ENV_PASSTHROUGH_ADDITIONS TS_AWS_CONFIG_DEF_REGION\"" >>"$POKY_DIR/oe-init-build-env"
    echo "export TS_RESOURCES_DIR=${EXTERNAL_OUT_DIR}" >>"$POKY_DIR/oe-init-build-env"
    echo "export BB_ENV_PASSTHROUGH_ADDITIONS=\"\$BB_ENV_PASSTHROUGH_ADDITIONS TS_RESOURCES_DIR\"" >>"$POKY_DIR/oe-init-build-env"

    # config variables
    local -r version_config="$VERSION_CONF"
    local -r all_environments_config="$CONFIGS_DIR/all/environments.conf"
    local -r target_environments_config="$CONFIGS_DIR/$TARGET/environments.conf"
    setup_environments_config $version_config
    setup_environments_config $all_environments_config
    setup_environments_config $target_environments_config
}

SHORT=t:,e,h
LONG=target:,env-override,as-source,help
OPTS=$(getopt -a --options $SHORT --longoptions $LONG -- "$@")

eval set -- "$OPTS"

ENV_OVERRIDE=false
AS_SOURCE=false

while :; do
    case "$1" in
    -t | --target)
        TARGET="$2"
        shift 2
        ;;
    -e | --env-override)
        ENV_OVERRIDE=true
        shift 1
        ;;
    --as-source)
        AS_SOURCE=true
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

if [ -z "$TARGET" ]; then
    help
    exit 1
fi

if [ ! -d "$CONFIGS_DIR/$TARGET" ]; then
    echo "ERROR: Target config directory ($CONFIGS_DIR/$TARGET) is not found."
    exit 1
fi

if [ "$AS_SOURCE" = false ]; then
    check_environments
    setup_repository "$CONFIGS_DIR/$TARGET/repo.conf"
    initialize_build_dir
    copy_configs
    setup_environments
    setup_external
    show_layers
fi
