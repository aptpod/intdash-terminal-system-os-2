========================================================================
 EP1-CH02A firmware release note    version: 2.3.2
========================================================================
------------------------------------------------------------------------
 Updating
------------------------------------------------------------------------
1. Clone device driver repository.

  $ git clone https://github.com/aptpod/apt-peripheral-linux-driver

2. Update the firmware with the following command:

  $ cd apt-peripheral-linux-driver
  $ sudo ./tools/apt_usbtrx_fwupdate.py --firmware EP1-CH02A_2.3.2.bin /dev/aptUSB0

------------------------------------------------------------------------
 Change log
------------------------------------------------------------------------
version 2.3.2
  - Fixed transmission status at startup.

version 2.3.1
  - 1st release.

------------------------------------------------------------------------
 Contact
------------------------------------------------------------------------
 aptpod,Inc.
   Web   : http://www.aptpod.co.jp
   E-Mail: product-support@aptpod.co.jp
