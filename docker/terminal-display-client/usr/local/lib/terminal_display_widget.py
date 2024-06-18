#!/usr/bin/env python3
# coding: utf-8

import hashlib
from dataclasses import dataclass, asdict, field
from typing import List, Tuple
import logging
from enum import Enum, IntEnum

import terminal_display_command as cmd

#
# Main Screen
#


class MainScreenIconType(Enum):
    MODE = "mode"
    QUEUE = "queue"
    NETWORK = "network"
    GPS = "gps"
    CAN = "can"
    CAMERA = "camera"


class MainScreenIconValueMode(IntEnum):
    # NOTE: Comment out unused enum
    NONE = 0
    # MEASURE_ALERT = 1
    # MEASURE_ERROR = 2
    MEASURE_OFF = 3
    MEASURE_ON = 4
    # RECOVER_ALERT = 5
    # RECOVER_ERROR = 6
    RECOVER_OFF = 7
    RECOVER_ON = 8


class MainScreenIconValueQueue(IntEnum):
    NONE = 0
    SIZE_OVER_1MB = 1
    SIZE_OVER_1GB = 2
    SIZE_0B = 3
    SIZE_UNDER_1MB = 4


class MainScreenIconValueGPS(IntEnum):
    NONE = 0
    FIX_2D = 1
    NO_FIX = 2
    OFF = 3
    FIX_3D = 4


class MainScreenIconValueNetwork(IntEnum):
    NONE = 0
    LAN_OFF = 1
    LAN_ON = 2
    SIM_00 = 3
    SIM_01 = 4
    SIM_02 = 5
    SIM_03 = 6
    SIM_04 = 7
    SIM_05 = 8
    WIFI_OFF = 9
    WIFI_ON = 10


class MainScreenIconValueCan(IntEnum):
    NONE = 0
    ALERT = 1
    ERROR = 2
    OFF = 3
    ON = 4


class MainScreenIconValueCamera(IntEnum):
    NONE = 0
    ALERT = 1
    ERROR = 2
    OFF = 3
    ON = 4


class ListScreenValueColorEnum(Enum):
    # NOTE: Comment out unused enum
    GREEN = "green"
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    # WHITE = "white"
    # BLUE = "blue"
    DARKGREY = "darkgrey"


class ListScreenValueColor:
    def from_bool(b: bool):
        return (
            ListScreenValueColorEnum.GREEN if b else ListScreenValueColorEnum.DARKGREY
        )

    def from_code(code: str, disconnected_color=ListScreenValueColorEnum.RED):
        if code == "connected":
            return ListScreenValueColorEnum.GREEN
        elif code == "quiet":
            return ListScreenValueColorEnum.ORANGE
        elif code == "disconnected":
            return disconnected_color
        elif code == "error":
            return ListScreenValueColorEnum.RED
        elif code == "none":
            return ListScreenValueColorEnum.DARKGREY
        else:
            return ListScreenValueColorEnum.RED

    def eq_str(s1: str, s2: str):
        return (
            ListScreenValueColorEnum.GREEN
            if s1 == s2
            else ListScreenValueColorEnum.DARKGREY
        )

    def ne_str_none(s: str):
        return (
            ListScreenValueColorEnum.GREEN
            if s != "none"
            else ListScreenValueColorEnum.DARKGREY
        )


@dataclass
class PageItem:
    key: str
    value: str
    color: ListScreenValueColorEnum = ListScreenValueColorEnum.GREEN
    error_msg: str = ""

    def is_error(self):
        return self.color == ListScreenValueColorEnum.RED


@dataclass
class PageItems:
    page_items: List[PageItem] = field(default_factory=list)

    def __iter__(self):
        yield from self.page_items

    def md5sum(self):
        page_items_dict = [asdict(item) for item in self.page_items]
        page_items_str = str(page_items_dict).encode()
        return hashlib.md5(page_items_str).hexdigest()

    def append(self, page_item: PageItem):
        self.page_items.append(page_item)


@dataclass
class MainScreenIcon:
    type: MainScreenIconType
    value: int
    page_item: PageItem


@dataclass
class MainScreenContent:
    icons: List[MainScreenIcon] = field(default_factory=list)

    def __iter__(self):
        yield from self.icons

    def md5sum(self):
        icons_dict = [asdict(icon) for icon in self.icons]
        icons_str = str(icons_dict).encode()
        return hashlib.md5(icons_str).hexdigest()

    def append(self, icon: MainScreenIcon):
        self.icons.append(icon)


class MainScreen:
    def __init__(self, cmd_send: cmd.CommandSender):
        self._cmd_send = cmd_send
        self.hash = None

    def update(self, content: MainScreenContent):
        if not content:
            return

        hash = content.md5sum()
        if self.hash == hash:
            return

        for icon in content:
            self._cmd_send.icon(icon.type.value, icon.value)

        self.hash = hash


#
# List Screen
#


@dataclass
class PageOptions:
    title: str
    index: int = 0


class Page:
    def __init__(self, options: PageOptions):
        self._options = options
        self.hash = None
        self.error_reported_flags = dict()

    def set_index(self, index):
        self._options.index = index

    def get_title(self):
        return self._options.title

    def build(self, cmd_send: cmd.CommandSender):
        cmd_send.set_page(self._options.index, self._options.title)

    def _check_error_report(self, cmd_send: cmd.CommandSender, item: PageItem):
        if item.is_error():
            if not self.error_reported_flags.get(item.key):
                if item.error_msg:
                    error_msg = item.error_msg
                else:
                    error_msg = f"{self._options.title}: {item.key} = {item.value}"

                cmd_send.error_log(error_msg)
                self.error_reported_flags[item.key] = True
        else:
            self.error_reported_flags[item.key] = False

    def update(self, cmd_send: cmd.CommandSender, page_items: PageItems):
        if not page_items:
            return

        hash = page_items.md5sum()
        if self.hash == hash:
            return

        logging.debug(f"UPDATE {self._options.title} page = {page_items}")
        cmd_send.edit_page(self._options.index)
        for item in page_items:
            cmd_send.set_key(
                self._options.index, item.key, item.value, item.color.value
            )
            self._check_error_report(cmd_send, item)
        cmd_send.edit_end(self._options.index)

        self.hash = hash

    def clear(self, cmd_send: cmd.CommandSender):
        cmd_send.edit_page(self._options.index)
        cmd_send.clr_page(self._options.index)
        cmd_send.edit_end(self._options.index)


PageContents = List[Tuple[Page, PageItems]]

UpdatedFlag = bool


@dataclass
class Collection:
    page: Page
    page_items: PageItems
    updated: bool


class ListScreen:
    def __init__(self, cmd_send: cmd.CommandSender):
        self._cmd_send = cmd_send
        self._collections: List[Collection] = list()
        self._page_num = 0

    def get_collections(self):
        return self._collections

    def append_page(self, page: Page, page_items: PageItems):
        if not page.get_title():
            return

        # set page index
        page.set_index(self._page_num)
        self._page_num += 1

        self._collections.append(Collection(page, page_items, False))
        logging.info(f"ListScreen {page.get_title()} page append")

    def build(self):
        self._cmd_send.progress(0, 1)
        self._cmd_send.beep(2, 100, 1)

        page_num = len(self._collections)

        self._cmd_send.set_page_num(page_num)
        for i, collection in enumerate(self._collections):
            collection.page.build(self._cmd_send)
            collection.page.update(self._cmd_send, collection.page_items)
            self._cmd_send.progress(i + 1, page_num)

        self._cmd_send.setup_end()
        self._cmd_send.beep(1, 200, 1)

    def update_page(self, update_page: Page, page_items: PageItems):
        for i, collection in enumerate(self._collections):
            # FIXME: Supports dynamically adding pages
            # Currently, only pages that exist at the time of build() execution can be updated.
            # If a page does not exist at the time of addition, we would like to support updating the page number before updating the page.
            if collection.page.get_title() == update_page.get_title():
                collection.page.update(self._cmd_send, page_items)
                self._collections[i].page_items = page_items
                self._collections[i].updated = True

    def delete_unupdated_page_items(self):
        for i, collection in enumerate(self._collections):
            if not collection.updated:
                collection.page.clear(self._cmd_send)
            self._collections[i].updated = False

    def is_error(self) -> bool:
        for collection in self.get_collections():
            for page_item in collection.page_items:
                if page_item.is_error():
                    return True
        return False
