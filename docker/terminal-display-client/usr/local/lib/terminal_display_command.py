#!/usr/bin/env python3
# coding: utf-8

import threading
import time
from datetime import datetime, timezone
import logging

import terminal_display_serial as serial


class CommandSender:
    def __init__(self, serial_option: serial.SerialOption, tz):
        self._serial = serial.Serial(serial_option)
        self._lock = threading.Lock()
        self._receive_ok = True
        self._cmd_id = 0
        self._tz = tz

    def _send_command(self, command):
        with self._lock:
            retry = 0
            # Send a command with @cmd_id for retransmission control.
            command = command + "@" + str(self._cmd_id)

            while retry < 3:
                logging.debug("[SEND]" + str(command))
                self._serial.write(str(command).encode())
                self._receive_ok = False  # Waiting to receive 'ACK' frm Display

                for i in range(200):
                    if self._receive_ok:
                        self._cmd_id = (self._cmd_id + 1) % 10
                        time.sleep(0.1)  # Make time to unlock the other thread
                        return True
                    else:
                        time.sleep(0.01)

                retry += 1
                logging.error("Timeout, try to resend")

        logging.error("Can't send command")
        logging.error("exit()")
        exit()

    def reset(self):
        logging.info("To reset esp32")
        self._serial.reset()
        logging.info("Waiting 5 sec...")
        time.sleep(5)

    def receive_ok(self):
        self._receive_ok = True

    def error_log(self, message):
        ts = datetime.now(self._tz).strftime("%H:%M:%S")
        command = '"error":{"time":"' + ts + '","log":"' + str(message) + '"}'
        self._send_command(command)

    def ping(self):
        return self._send_command('"ping"')

    def init(self):
        return self._send_command('"init"')

    def progress(self, current, all):
        percent = int(float(current / all) * 100)
        return self._send_command('"progress":"{0}"'.format(percent))

    def set_page_num(self, page_num):
        return self._send_command('"setpagenum":"{0}"'.format(page_num))

    def set_page(self, index, title):
        max_len = 28
        if len(title) > max_len:
            logging.debug(f"title is too long. strip title. {title}")
            title = title[:max_len]
        return self._send_command(
            '"setpage":{{"page":"{0}","title":"{1}"}}'.format(index, title)
        )

    def clr_page(self, index):
        return self._send_command('"clrpageline":"{0}"'.format(index))

    def edit_page(self, index):
        return self._send_command('"edit_page":"{0}"'.format(index))

    def edit_end(self, index):
        return self._send_command('"edit_end":"{0}"'.format(index))

    def set_key(self, page, key, value, color):
        if not value:
            value = ""

        max_len = 24
        if len(key) + 1 + len(value) > max_len:
            logging.debug(f"key and value are too long. strip value. {key}:{value}")
            value_len_strip = max_len - len(key) - 1
            value = value[:value_len_strip]
        return self._send_command(
            '"setkey":{{"page":"{0}","key":"{1}","value":"{2}","color":"{3}"}}'.format(
                page, key, value, color
            )
        )

    def setup_end(self):
        self._send_command('"setup_end"')

    def icon(self, key, value):
        return self._send_command(f'"{key}":"{value}"')

    def update_cmd(self, page, key, value, color):
        cmd = 'update:"page":"{0}","key":"{1}","value":"{2}","color":"{3}"'.format(
            page, key, value, color
        )
        self._send_command(cmd)

    def set_vol(self, vol):
        return self._send_command('"set_vol":"{}"'.format(vol))

    def beep(self, count, dur, tone):
        return self._send_command(
            '"beep":{{"dur":"{0}","tone":"{1}","cnt":"{2}"}}'.format(dur, tone, count)
        )

    def ctrl_led(self, led_type, led, on):
        return self._send_command(
            '"ctrl_led":{{"type":"{0}","led":"{1}","on":"{2}"}}'.format(
                led_type, led, on
            )
        )

    def version(self):
        return self._send_command('"version"')


class CommandReceiver:
    def __init__(self, serial_option: serial.SerialOption):
        self._serial = serial.Serial(serial_option)

    def readline(self):
        return self._serial.readline()
