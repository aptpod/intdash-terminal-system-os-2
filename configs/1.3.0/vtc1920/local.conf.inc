
#
# Machine Selection
#
# Intel Atom® x7211RE - Elkhart Lake
MACHINE = "intel-skylake-64"
MACHINEOVERRIDES =. "vtc1920:"

#
# Machine-specific Mender Settings
#
MENDER_DEVICE_TYPE:intel-skylake-64 = "vtc1920"
MENDER_STORAGE_DEVICE = "/dev/sda"
MENDER_STORAGE_TOTAL_SIZE_MB = "8192"
IMAGE_FSTYPES += " hddimg"
MENDER_FEATURES_ENABLE:append = " mender-growfs-data"

# FIXME: WORKAROUND
# In mender-part-images.bbclass, the appropriate .bz2 type should be added to IMAGE_FSTYPES,
# but with the current configuration, it is not added automatically.
# Therefore, it is explicitly set in local.conf.
# Depending on updates to meta-mender, this append may become unnecessary in the future.
IMAGE_FSTYPES:append = " uefiimg.bz2"

## provisioning support
IMAGE_CLASSES += "ts2-provisioning-config"

# Default GPS Settings
DEFAULT_GPS_DEVICE_PATH = "/dev/ttyS3"
DEFAULT_GPS_NMEA_BAUDRATE = "38400"
DEFAULT_GPS_UBX_BAUDRATE = "57600"
DEFAULT_GPS_MESSAGE_TYPE = "ubx"
DEFAULT_PPS_DEVICE_PATH = ""
