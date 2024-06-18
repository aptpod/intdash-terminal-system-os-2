========================================================================
 EP1-AG08A firmware release note    version: 1.0.2
========================================================================
------------------------------------------------------------------------
 Updating
------------------------------------------------------------------------
1. Clone device driver repository.

  $ git clone https://github.com/aptpod/apt-peripheral-linux-driver

2. Update the firmware with the following command:

  $ cd apt-peripheral-linux-driver
  $ sudo ./tools/apt_usbtrx_fwupdate.py --firmware EP1-AG08A_1.0.2.bin /dev/aptUSB0

------------------------------------------------------------------------
 Change log
------------------------------------------------------------------------
version 1.0.2
  - 1st release.

------------------------------------------------------------------------
 Contact
------------------------------------------------------------------------
 aptpod,Inc.
   Web   : http://www.aptpod.co.jp
   E-Mail: product-support@aptpod.co.jp
