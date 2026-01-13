
#
# Machine Selection
#
MACHINE = "jasmine"

#
# Machine-specific Mender Settings
#
INHERIT:append:tegra = " tegra-mender-setup"
PREFERRED_PROVIDER_virtual/bootloader:tegra186 = "cboot-t18x"
MENDER_DATA_PART_SIZE_MB_DEFAULT:jasmine = "2048"
## serial number support
IMAGE_CLASSES += "image_types_tegra_serial_number"
MENDER_DEVICE_TYPE:jasmine = "edgeplant-t1"

# support gstreamer in docker
require conf/include/gstreamer-1.14.conf
