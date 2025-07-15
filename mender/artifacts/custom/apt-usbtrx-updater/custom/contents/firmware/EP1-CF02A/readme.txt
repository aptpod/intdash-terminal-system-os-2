========================================================================
 EP1-CF02A firmware release note
========================================================================
------------------------------------------------------------------------
 Updating
------------------------------------------------------------------------
1. Clone device driver repository.

  $ git clone https://github.com/aptpod/apt-peripheral-linux-driver

2. Update the firmware with the following command:

  $ cd apt-peripheral-linux-driver
  $ sudo ./tools/apt_usbtrx_fwupdate.py --firmware EP1-CF02A_X.X.X.bin /dev/aptUSB0

------------------------------------------------------------------------
 Contact
------------------------------------------------------------------------
 aptpod,Inc.
   Web   : http://www.aptpod.co.jp
   E-Mail: product-support@aptpod.co.jp
