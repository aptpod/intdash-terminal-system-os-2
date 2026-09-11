# Mender Artifact Configuration
# Edit the variables below and run generate.sh to create an artifact.

ARTIFACT_NAME="sample"

# Set version string (e.g., "1.0.0"). Leave empty ("") to create an uninstaller.
ARTIFACT_VERSION="1.0.0"

# Preserve version inventory after OS updates.
SOFTWARE_FILESYSTEM="data-partition"

# Target device types (arch):
#   edgeplant-t1 (arm64), edgeplant-r1 (arm64), raspberrypi4-64 (arm64), vtc1920 (amd64)
#
# Examples:
#   DEVICE_TYPES=("edgeplant-t1")
#   DEVICE_TYPES=("edgeplant-t1" "raspberrypi4-64")
DEVICE_TYPES=()
