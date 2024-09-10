
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
VIDEO_CAMERA = "1"
GPU_MEM = "128"
RASPBERRYPI_CAMERA_V2 = "1"
RASPBERRYPI_CAMERA_V3 = "1"

# In Terminal System 2, the kernel is updated regularly.
# By enabling 'rpi-update-firmware', we accept the risk of the device failing to boot due to issues such as power outages,
# and proceed to activate the update of the boot partition.
INHERIT += "rpi-update-firmware"
