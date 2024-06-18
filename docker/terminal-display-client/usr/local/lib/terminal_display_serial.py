#!/usr/bin/env python3
# coding: utf-8

import serial
import threading
import time
import logging
from dataclasses import dataclass


@dataclass
class SerialOption:
    port: str
    baudrate: int
    timeout: float


class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class Serial(metaclass=SingletonMeta):
    def __init__(self, option: SerialOption):
        self._ser = serial.Serial(option.port, option.baudrate, timeout=option.timeout)
        self._write_lock = threading.Lock()
        self._read_lock = threading.Lock()

    def reset(self):
        self._ser.setDTR(False)
        time.sleep(0.1)
        self._ser.setRTS(False)
        self._ser.rtscts = False

    def write(self, data):
        with self._write_lock:
            logging.debug(f"write: {data}")
            self._ser.write(data)

    def readline(self):
        with self._read_lock:
            logging.debug(f"readline")
            return self._ser.readline()
