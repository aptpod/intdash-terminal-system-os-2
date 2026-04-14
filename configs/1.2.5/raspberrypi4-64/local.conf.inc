
#
# Machine Selection
#
MACHINE = "raspberrypi4-64"

#
# Machine-specific Mender Settings
#
# Appended fragment from meta-mender-community/meta-mender-raspberrypi/templates
RPI_USE_U_BOOT = "1"
ENABLE_UART = "1"
MENDER_STORAGE_TOTAL_SIZE_MB = "8192"
MENDER_BOOT_PART_SIZE_MB = "64"
IMAGE_INSTALL:append = " kernel-image kernel-devicetree"
IMAGE_FSTYPES:remove = " rpi-sdimg"
MENDER_FEATURES_ENABLE:append = " mender-uboot mender-image-sd"
MENDER_FEATURES_DISABLE:append = " mender-grub mender-image-uefi"

# FIXME: WORKAROUND
# In mender-part-images.bbclass, the appropriate .bz2 type should be added to IMAGE_FSTYPES,
# but with the current configuration, it is not added automatically.
# Therefore, it is explicitly set in local.conf.
# Depending on updates to meta-mender, this append may become unnecessary in the future.
IMAGE_FSTYPES:append = " sdimg.bz2"

## provisioning support
IMAGE_CLASSES += "ts2-provisioning-config"
TS2_PROVISIONING_CONFIG_DIR = "${MENDER_BOOT_PART_MOUNT_LOCATION}"
TS2_PROVISIONING_CONFIG_DEPLOY_DIR_NAME = "${BOOTFILES_DIR_NAME}"
TS2_PROVISIONING_CONFIG_SERIAL_NUMBER_REQUIRED = "0"
TS2_PROVISIONING_CONFIG_SERIAL_NUMBER_DEFAULT = "$(awk "/Serial/ {print \\$3}" /proc/cpuinfo)"
TS2_PROVISIONING_CONFIG_SERIAL_NUMBER_DEFAULT_DESCRIPTION = "<raspberry pi serial>"

#
# Build Options
#
# https://meta-raspberrypi.readthedocs.io/en/latest/extra-build-config.html
# Enable SPI bus
ENABLE_SPI_BUS = "1"
# Enable I2C
ENABLE_I2C = "1"
KERNEL_MODULE_AUTOLOAD:rpi += "i2c-dev i2c-bcm2708"
# GPIO Shutdown
ENABLE_GPIO_SHUTDOWN = "1"
GPIO_SHUTDOWN_PIN = "25"
# HDMI
HDMI_FORCE_HOTPLUG = "1"
# Raspberry Pi Camera Module
# camera_auto_detect=1 is set in meta-terminal-system
GPU_MEM = "128"
# https://meta-raspberrypi.readthedocs.io/en/latest/ipcompliance.html#linux-firmware-rpidistro
LICENSE_FLAGS_ACCEPTED:append = "synaptics-killswitch"

# In Terminal System 2, the kernel is updated regularly.
# By enabling 'rpi-update-firmware', we accept the risk of the device failing to boot due to issues such as power outages,
# and proceed to activate the update of the boot partition.
#INHERIT += "rpi-update-firmware"
# FIXME: WORKAROUND
# Revert the following commit due to a failure in updating the OS on Raspberry Pi 4.
# https://github.com/mendersoftware/meta-mender-community/pull/395
INHERIT += "rpi-update-firmware-rpi4-workaround"
