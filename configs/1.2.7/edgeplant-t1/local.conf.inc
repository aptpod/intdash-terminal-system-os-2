
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

# Default GPS Settings
DEFAULT_GPS_DEVICE_PATH = "/dev/ttyTHS1"
DEFAULT_GPS_NMEA_BAUDRATE = "9600"
DEFAULT_GPS_UBX_BAUDRATE = "57600"
DEFAULT_GPS_MESSAGE_TYPE = "ubx"
DEFAULT_PPS_DEVICE_PATH = "/dev/pps0"
