=========================================================================
 ET1-128NJA Power Management MCU firmware release note    version: 1.3.1
=========================================================================
-------------------------------------------------------------------------
 Updating
-------------------------------------------------------------------------
1. Update the firmware with the following command:

   $ sudo edgeplant-l4t-tools
     ================================================================================
      EDGEPLANT L4T TOOLS
     ================================================================================
     Choose a number or Enter 'q' for exit

     --------------------------------------------------------------------------------
      Select the target board
     --------------------------------------------------------------------------------
     1) EDGEPLANT T1
     Enter: 1
     --------------------------------------------------------------------------------
      Select function
     --------------------------------------------------------------------------------
     1) Update dtb,
     2) Update powermanage,
     3) Change HDMI RGB range
     Enter: 2
     Update file path: ./ET1-128NJA_pmmcu_1.3.1.bin

2. Power off and on after updating. The power management firmware will be upgraded after poweroff.

-------------------------------------------------------------------------
 Change log
-------------------------------------------------------------------------
version 1.3.1
  - Fixed I/O expander reset process

version 1.3.0
  - Add fault logging

version 1.2.1
  - Reset if I/O expander is unstable

version 1.2.0
  - Reduce dark current
  - Enhance Wake on CAN
    - Power on and off with a specific CAN packet

version 1.1.0
  - Add Wake on CAN

-------------------------------------------------------------------------
 Contact
-------------------------------------------------------------------------
 aptpod,Inc.
   Web   : http://www.aptpod.co.jp
   E-Mail: product-support@aptpod.co.jp
