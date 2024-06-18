#!/usr/bin/env python3
__version__ = "1.7.0"

import time
import threading
import re
from enum import Enum, auto
from stat import *
from datetime import timedelta, timezone
from optparse import OptionParser
import configparser as ConfigParser
import logging
from distutils.util import strtobool
import os
import atexit

import terminal_display_backend as bk
from terminal_display_command import *
import terminal_display_widget as widget
import terminal_display_serial as serial


DEFAULT_CONFIG_FILE = "terminal-display.cfg"
FW_VERSION_FILE_PATH = "/run/terminal-display/firmware_version"
LOGGING_FORMAT_INFO = "[%(levelname)s] %(message)s"
LOGGING_FORMAT_DEBUG = "[%(levelname)s] %(funcName)s():%(lineno)d :%(message)s"


@atexit.register
def remove_version_file():
    if os.path.exists(FW_VERSION_FILE_PATH):
        os.remove(FW_VERSION_FILE_PATH)


class Backend:
    def __init__(self, base_uri):
        self.api_client = bk.TerminalSystemAPIClient(base_uri)
        self.backend = bk.TerminalDisplayBackend(self.api_client)
        self.get_funcs = {
            "connection": self._get_connection,
            "stream": self._get_stream,
            "upstreams": self._get_upstreams,
            "downstreams": self._get_downstreams,
            "deferred_upload": self._get_deferred_upload,
            "daemon": self._get_daemon,
            "network": self._get_network,
            "device_connectors": self._get_device_connectors,
            "can_state": self._get_can_state,
            "camera_state": self._get_camera_state,
            "gps_state": self._get_gps_state,
            "hardware_info": self._get_hardware_info,
        }
        self.post_funcs = {
            "start_agent_streamer": self._post_start_agent_streamer,
            "stop_agent_streamer": self._post_stop_agent_streamer,
        }

    def get(self, endpoint):
        obj, success = self.get_funcs[endpoint]()
        if not success:
            logging.error(f"get {endpoint} failed")
        return obj, success

    def post(self, endpoint):
        success = self.post_funcs[endpoint]()
        if not success:
            logging.error(f"post {endpoint} failed")
        return success

    def _get_connection(self):
        return self.backend.get_connection()

    def _get_stream(self):
        return self.backend.get_stream()

    def _get_upstreams(self):
        return self.backend.get_upstreams()

    def _get_downstreams(self):
        return self.backend.get_downstreams()

    def _get_deferred_upload(self):
        return self.backend.get_deferred_upload()

    def _get_daemon(self):
        return self.backend.get_daemon_state()

    def _get_network(self):
        return self.backend.get_network_state()

    def _get_device_connectors(self):
        return self.backend.get_device_connectors()

    def _get_can_state(self):
        return self.backend.get_device_connector_can_state()

    def _get_camera_state(self):
        return self.backend.get_device_connector_camera_state()

    def _get_gps_state(self):
        return self.backend.get_device_connector_gps_state()

    def _get_hardware_info(self):
        return self.backend.get_hardware_info()

    def _post_start_agent_streamer(self):
        return self.backend.start_agent_streamer()

    def _post_stop_agent_streamer(self):
        return self.backend.stop_agent_streamer()


class ApiResponse:
    def __init__(self, backend):
        self._backend = backend
        self._responses = dict()
        self._endpoint_list: dict = {
            "connection": "connection",
            "stream": "stream",
            "upstreams": "upstreams",
            "downstreams": "downstreams",
            "deferred_upload": "deferred_upload",
            "daemon": "daemon",
            "network": "network",
            "device_connectors": "device_connectors",
            "gps_state": "gps_state",
            "can_state": "can_state",
            "camera_state": "camera_state",
            "hardware_info": "hardware_info",
        }

    def update(self):
        for endpoint in self._endpoint_list:
            self._responses[endpoint], success = self._backend.get(endpoint)
            if not success:
                self._responses[endpoint] = {}

    def connection(self):
        return self._responses.get("connection")

    def stream(self):
        return self._responses.get("stream")

    def upstreams(self):
        return self._responses.get("upstreams")

    def downstreams(self):
        return self._responses.get("downstreams")

    def deferred_upload(self):
        return self._responses.get("deferred_upload")

    def daemon(self):
        return self._responses.get("daemon")

    def network(self):
        return self._responses.get("network")

    def gps_state(self):
        return self._responses.get("gps_state")

    def device_connectors(self):
        return self._responses.get("device_connectors")

    def can_state(self):
        return self._responses.get("can_state")

    def camera_state(self):
        return self._responses.get("camera_state")

    def hardware_info(self):
        return self._responses.get("hardware_info")


class QueueState(Enum):
    NOT_INITIALIZED = auto()
    EMPTY = auto()
    SOME = auto()


class TerminalDisplayClient:
    def __init__(self, config_file):
        try:
            self._config_file = config_file
            self._config = ConfigParser.ConfigParser()
            self._config.read(self._config_file)
        except:
            logging.error("can't open setting file:" + self._config_file)
            exit()

        try:
            log_level = self._config.get("general", "log_level")
            if log_level.upper() == "DEBUG":
                logging.basicConfig(
                    level=logging.DEBUG, format=LOGGING_FORMAT_DEBUG, force=True
                )
        except:
            logging.error("can't read debug flag. set to Enable debug log")

        # setup serial port
        try:
            serial_path = self._config.get("general", "serial_path")
            reset = self._config.get("general", "reset")
            logging.info("reset esp32:{}".format(reset))
            logging.info("open serial:{}".format(serial_path))
        except:
            logging.error("can't read setting file:" + self._config_file)

        try:
            tz = self._config.get("m5stack", "time_zone")
            tz = timezone(timedelta(hours=int(tz)))
            serial_option = serial.SerialOption(serial_path, 115200, None)
            self._cmd_sender = CommandSender(serial_option, tz)
            self._cmd_receiver = CommandReceiver(serial_option)
            if reset == "yes":
                self._cmd_sender.reset()
        except:
            logging.error("Can not open serial device")
            logging.error("exit()")
            exit()

        base_uri = self._config.get("general", "api_url")

        self._backend = Backend(base_uri)
        self._recover_flg = False
        self._restart_service_flg = False
        self._beep_flag_error = False
        self._beep_flag_deferred_uploading = False
        self._beep_flag_deferred_upload_complete = False
        self._queue_state = QueueState.NOT_INITIALIZED

        self._th_list = list()
        th = threading.Thread(target=self._recv_thread, daemon=True)
        self._th_list.append(th)
        th = threading.Thread(target=self._ping_thread, daemon=True)
        self._th_list.append(th)
        th = threading.Thread(target=self._api_thread, daemon=True)
        self._th_list.append(th)
        th = threading.Thread(target=self._beep_thread, daemon=True)
        self._th_list.append(th)

    def _beep_thread(self):
        volume = self._config.get("m5stack", "volume")
        logging.info("volume :" + volume)
        self._cmd_sender.set_vol(volume)

        logging.info("Start beep_thread()")
        while True:
            if self._beep_flag_error:
                self._cmd_sender.beep(2, 50, 2)
                self._beep_flag_error = False
                time.sleep(1)

            if self._beep_flag_deferred_uploading:
                self._cmd_sender.beep(1, 30, 1)
                time.sleep(1)

            if self._beep_flag_deferred_upload_complete:
                self._cmd_sender.beep(5, 500, 1)
                self._beep_flag_deferred_upload_complete = False
                time.sleep(1)

            time.sleep(0.5)

    def _ping_thread(self):
        logging.info("Start ping_thread()")
        while True:
            self._cmd_sender.ping()
            # Timeout is 10 seconds
            time.sleep(5)

    def _collect_main_screen_content_mode(self, stream, daemon):
        page_item = widget.PageItem(
            "Mode", "none", widget.ListScreenValueColorEnum.DARKGREY
        )

        if not stream or not daemon:
            return widget.MainScreenIcon(
                widget.MainScreenIconType.MODE,
                widget.MainScreenIconValueMode.RECOVER_OFF,
                page_item,
            )

        stream_state = stream.get("state")
        daemon_state = daemon.get("state")

        if stream_state != "none":
            value = widget.MainScreenIconValueMode.MEASURE_ON
            page_item.value = "Running"
            page_item.color = widget.ListScreenValueColorEnum.GREEN
        else:
            if daemon_state == "connected":
                value = widget.MainScreenIconValueMode.RECOVER_ON
                page_item.value = "Deferred Uploading"
                page_item.color = widget.ListScreenValueColorEnum.GREEN
            else:
                value = widget.MainScreenIconValueMode.RECOVER_OFF
                page_item.value = "Stopped"
                page_item.color = widget.ListScreenValueColorEnum.DARKGREY

        return widget.MainScreenIcon(widget.MainScreenIconType.MODE, value, page_item)

    def _collect_main_screen_content_queue(self, daemon):
        page_item = widget.PageItem(
            "Queue", "none", widget.ListScreenValueColorEnum.DARKGREY
        )

        if not daemon:
            return widget.MainScreenIcon(
                widget.MainScreenIconType.QUEUE,
                widget.MainScreenIconValueQueue.SIZE_0B,
                page_item,
            )

        pending_data_size = daemon.get("pending_data_size")

        if pending_data_size > 1024 * 1024 * 1024:
            value = widget.MainScreenIconValueQueue.SIZE_OVER_1GB
            page_item.value = "{:.1f} GB".format(
                pending_data_size / (1024 * 1024 * 1024)
            )
            page_item.color = widget.ListScreenValueColorEnum.GREEN
        elif pending_data_size > 1024 * 1024:
            value = widget.MainScreenIconValueQueue.SIZE_OVER_1MB
            page_item.value = "{:.1f} MB".format(pending_data_size / (1024 * 1024))
            page_item.color = widget.ListScreenValueColorEnum.GREEN
        elif pending_data_size > 0:
            value = widget.MainScreenIconValueQueue.SIZE_UNDER_1MB
            page_item.value = "{:.1f} KB".format(pending_data_size / (1024))
            page_item.color = widget.ListScreenValueColorEnum.GREEN
        else:
            value = widget.MainScreenIconValueQueue.SIZE_0B
            page_item.value = "{0} Byte".format(pending_data_size)
            page_item.color = widget.ListScreenValueColorEnum.DARKGREY

        return widget.MainScreenIcon(widget.MainScreenIconType.QUEUE, value, page_item)

    def _rssi_to_icon_value(self, rssi: int) -> widget.MainScreenIconValueNetwork:
        if rssi == 0:
            # NOTE: Icons are valid even if RSSI cannot be obtained
            return widget.MainScreenIconValueNetwork.SIM_05
        elif rssi <= -93:
            return widget.MainScreenIconValueNetwork.SIM_00
        elif rssi <= -85:
            return widget.MainScreenIconValueNetwork.SIM_01
        elif rssi <= -77:
            return widget.MainScreenIconValueNetwork.SIM_02
        elif rssi <= -69:
            return widget.MainScreenIconValueNetwork.SIM_03
        elif rssi <= -61:
            return widget.MainScreenIconValueNetwork.SIM_04
        else:
            return widget.MainScreenIconValueNetwork.SIM_05

    def _rssi_to_page_item(self, rssi: int) -> widget.PageItem:
        icon_value = self._rssi_to_icon_value(rssi)

        if rssi == 0:
            value = "none"
            color = widget.ListScreenValueColorEnum.DARKGREY
        else:
            value = str(rssi)
            if icon_value == widget.MainScreenIconValueNetwork.SIM_00:
                color = widget.ListScreenValueColorEnum.RED
            elif icon_value == widget.MainScreenIconValueNetwork.SIM_01:
                color = widget.ListScreenValueColorEnum.RED
            elif icon_value == widget.MainScreenIconValueNetwork.SIM_02:
                color = widget.ListScreenValueColorEnum.YELLOW
            elif icon_value == widget.MainScreenIconValueNetwork.SIM_03:
                color = widget.ListScreenValueColorEnum.YELLOW
            elif icon_value == widget.MainScreenIconValueNetwork.SIM_04:
                color = widget.ListScreenValueColorEnum.GREEN
            elif icon_value == widget.MainScreenIconValueNetwork.SIM_05:
                color = widget.ListScreenValueColorEnum.GREEN
            else:
                color = widget.ListScreenValueColorEnum.DARKGREY

        return widget.PageItem("RSSI", value, color)

    def _collect_main_screen_content_network(self, network):
        page_item = widget.PageItem(
            "Network", "none", widget.ListScreenValueColorEnum.DARKGREY
        )

        if not network:
            return widget.MainScreenIcon(
                widget.MainScreenIconType.NETWORK,
                widget.MainScreenIconValueNetwork.LAN_OFF,
                page_item,
            )

        current_device_type = network.get("current_device", {}).get("device_type")
        if not current_device_type:
            return widget.MainScreenIcon(
                widget.MainScreenIconType.NETWORK,
                widget.MainScreenIconValueNetwork.LAN_OFF,
                page_item,
            )

        page_item.value = current_device_type
        page_item.color = widget.ListScreenValueColorEnum.GREEN

        if current_device_type == "ethernet":
            value = widget.MainScreenIconValueNetwork.LAN_ON
        elif current_device_type == "wifi":
            value = widget.MainScreenIconValueNetwork.WIFI_ON
        elif current_device_type == "modem":
            rssi = network.get("gsm_state", {}).get("rssi")
            value = self._rssi_to_icon_value(rssi)
        else:
            logging.error(f"invalid current_device_type: {current_device_type}")
            value = widget.MainScreenIconValueNetwork.LAN_OFF

        return widget.MainScreenIcon(
            widget.MainScreenIconType.NETWORK, value, page_item
        )

    def _collect_main_screen_content_gps(self, gps_state):
        page_item = widget.PageItem(
            "GPS", "none", widget.ListScreenValueColorEnum.DARKGREY
        )

        if not gps_state:
            return widget.MainScreenIcon(
                widget.MainScreenIconType.GPS,
                widget.MainScreenIconValueGPS.OFF,
                page_item,
            )

        state = gps_state.get("state")
        quality = gps_state.get("quality")

        if state == "none":
            value = widget.MainScreenIconValueGPS.OFF
            page_item.value = state
            page_item.color = widget.ListScreenValueColorEnum.DARKGREY
        else:
            page_item.value = quality
            if quality == "no_fix" or quality == "time_only_fix":
                value = widget.MainScreenIconValueGPS.NO_FIX
                page_item.color = widget.ListScreenValueColorEnum.RED
            elif quality == "2d_fix" or quality == "dead_reckoning_only":
                value = widget.MainScreenIconValueGPS.FIX_2D
                page_item.color = widget.ListScreenValueColorEnum.ORANGE
            elif quality == "3d_fix" or quality == "gps_+_dead_reckoning":
                value = widget.MainScreenIconValueGPS.FIX_3D
                page_item.color = widget.ListScreenValueColorEnum.GREEN
            elif quality == "none":
                value = widget.MainScreenIconValueGPS.OFF
                page_item.color = widget.ListScreenValueColorEnum.DARKGREY
            else:
                logging.error(f"invalid gps quality: {quality}")
                value = widget.MainScreenIconValueGPS.NO_FIX
                page_item.color = widget.ListScreenValueColorEnum.RED

        return widget.MainScreenIcon(widget.MainScreenIconType.GPS, value, page_item)

    def _collect_main_screen_content_can(self, can_state):
        page_item = widget.PageItem(
            "CAN", "none", widget.ListScreenValueColorEnum.DARKGREY
        )

        if not can_state:
            return widget.MainScreenIcon(
                widget.MainScreenIconType.CAN,
                widget.MainScreenIconValueCan.OFF,
                page_item,
            )

        state = can_state.get("state")
        page_item.value = state
        page_item.color = widget.ListScreenValueColor.from_code(state)

        if state == "connected":
            value = widget.MainScreenIconValueCan.ON
        elif state == "quiet":
            value = widget.MainScreenIconValueCan.ALERT
        elif state == "disconnected":
            value = widget.MainScreenIconValueCan.ERROR
        elif state == "none":
            value = widget.MainScreenIconValueCan.OFF
        else:
            logging.error(f"invalid can state: {state}")
            value = widget.MainScreenIconValueCan.ERROR

        return widget.MainScreenIcon(widget.MainScreenIconType.CAN, value, page_item)

    def _collect_main_screen_content_camera(self, camera_state):
        page_item = widget.PageItem(
            "Camera", "none", widget.ListScreenValueColorEnum.DARKGREY
        )

        if not camera_state:
            return widget.MainScreenIcon(
                widget.MainScreenIconType.CAMERA,
                widget.MainScreenIconValueCamera.OFF,
                page_item,
            )

        state = camera_state.get("state")
        page_item.value = state
        page_item.color = widget.ListScreenValueColor.from_code(state)

        if state == "connected":
            value = widget.MainScreenIconValueCamera.ON
        elif state == "quiet":
            # quiet is an error for camera
            value = widget.MainScreenIconValueCamera.ERROR
        elif state == "disconnected":
            value = widget.MainScreenIconValueCamera.ERROR
        elif state == "none":
            value = widget.MainScreenIconValueCamera.OFF
        else:
            logging.error(f"invalid camera state: {state}")
            value = widget.MainScreenIconValueCamera.ERROR

        return widget.MainScreenIcon(widget.MainScreenIconType.CAMERA, value, page_item)

    def _collect_main_screen_content(self, api_response: ApiResponse):
        mode = self._collect_main_screen_content_mode(
            api_response.stream(), api_response.daemon()
        )
        queue = self._collect_main_screen_content_queue(api_response.daemon())
        network = self._collect_main_screen_content_network(api_response.network())
        gps = self._collect_main_screen_content_gps(api_response.gps_state())
        can = self._collect_main_screen_content_can(api_response.can_state())
        camera = self._collect_main_screen_content_camera(api_response.camera_state())

        content = widget.MainScreenContent()
        content.append(mode)
        content.append(queue)
        content.append(network)
        content.append(gps)
        content.append(can)
        content.append(camera)

        return content

    def _collect_top_page_items(self, api_response: ApiResponse):
        mode = self._collect_main_screen_content_mode(
            api_response.stream(), api_response.daemon()
        )
        queue = self._collect_main_screen_content_queue(api_response.daemon())
        network = self._collect_main_screen_content_network(api_response.network())
        gps = self._collect_main_screen_content_gps(api_response.gps_state())
        can = self._collect_main_screen_content_can(api_response.can_state())
        camera = self._collect_main_screen_content_camera(api_response.camera_state())

        page_items = widget.PageItems()
        page_items.append(mode.page_item)
        page_items.append(queue.page_item)
        page_items.append(network.page_item)
        page_items.append(gps.page_item)
        page_items.append(can.page_item)
        page_items.append(camera.page_item)

        return page_items

    def _collect_network_page_contents(self, api_response: ApiResponse):
        network_page_contents: widget.PageContents = list()

        api_response_network = api_response.network()

        current_device_name = api_response_network.get("current_device", {}).get(
            "device_name", ""
        )

        devices = api_response_network.get("devices")
        if not devices:
            return network_page_contents

        connections = api_response_network.get("connections")
        if not connections:
            return network_page_contents

        for connection in connections:
            enabled = connection.get("enabled")

            device = [
                i for i in devices if i["device_name"] == connection["device_name"]
            ]
            if not device:
                continue
            device = device[0]

            # common items
            connection_type = connection.get("connection_type")
            display_name = connection.get("display_name")
            title = f"Network {connection_type} {display_name}"

            device_name = connection.get("device_name")

            ip_address = device.get("ip_address")
            ip_address_error_msg = ""
            if ip_address:
                gateway = device.get("gateway")
                if gateway:
                    ip_address_color = widget.ListScreenValueColorEnum.GREEN
                else:
                    ip_address_color = widget.ListScreenValueColorEnum.RED
                    ip_address_error_msg = "gateway not found"
            else:
                ip_address = "Not Connected"
                if enabled and connection_type != "ethernet":
                    ip_address_color = widget.ListScreenValueColorEnum.RED
                else:
                    ip_address_color = widget.ListScreenValueColorEnum.DARKGREY

            page = widget.Page(widget.PageOptions(title))
            page_items = widget.PageItems()
            page_items.append(
                widget.PageItem(
                    "Device",
                    device_name,
                    widget.ListScreenValueColor.eq_str(
                        device_name, current_device_name
                    ),
                )
            )
            page_items.append(
                widget.PageItem(
                    "IP", ip_address, ip_address_color, ip_address_error_msg
                )
            )

            # connection depend items
            if connection_type == "ethernet":
                pass
            elif connection_type == "wireless":
                wireless_settings = connection.get("wireless_settings")
                ssid = wireless_settings.get("ssid")
                page_items.append(widget.PageItem("SSID", ssid))
            elif connection_type == "wireless_access_point":
                pass
            elif connection_type == "gsm":
                gsm_settings = connection.get("gsm_settings")
                apn = gsm_settings.get("apn")

                gsm_state = api_response_network.get("gsm_state")
                carrier = gsm_state.get("carrier")
                rssi = gsm_state.get("rssi")
                mode = gsm_state.get("mode")

                page_items.append(widget.PageItem("APN", apn))
                page_items.append(
                    widget.PageItem(
                        "Carrier",
                        carrier,
                        widget.ListScreenValueColor.ne_str_none(carrier),
                    )
                )
                page_items.append(
                    widget.PageItem(
                        "Mode", mode, widget.ListScreenValueColor.ne_str_none(mode)
                    )
                )
                page_items.append(self._rssi_to_page_item(rssi))

            network_page_contents.append((page, page_items))

        return network_page_contents

    def _collect_agent_page_contents(self, api_response: ApiResponse):
        agent_page_contents: widget.PageContents = list()

        upstreams = api_response.upstreams()
        downstreams = api_response.downstreams()
        deferred_upload = api_response.deferred_upload()

        for upstream in upstreams:
            id = upstream.get("id")
            # settings
            enabled = upstream.get("enabled")
            persist = upstream.get("persist_realtime_data")
            recover = upstream.get("deferred_upload")
            qos = upstream.get("qos")

            # state
            code = upstream.get("code", "none")
            error = upstream.get("error", "none")

            title = f"Agent Up {id}"
            if code == "error":
                status = error
            else:
                status = code

            page = widget.Page(widget.PageOptions(title))
            page_items = widget.PageItems()
            page_items.append(
                widget.PageItem(
                    "Status", status, widget.ListScreenValueColor.from_code(code)
                )
            )
            page_items.append(
                widget.PageItem(
                    "Enabled",
                    str(enabled),
                    widget.ListScreenValueColor.from_bool(enabled),
                )
            )
            page_items.append(
                widget.PageItem(
                    "Persist",
                    str(persist),
                    widget.ListScreenValueColor.from_bool(persist),
                )
            )
            page_items.append(
                widget.PageItem(
                    "DeferredUpload",
                    str(recover),
                    widget.ListScreenValueColor.from_bool(recover),
                )
            )
            page_items.append(widget.PageItem("QoS", qos))

            agent_page_contents.append((page, page_items))

        for downstream in downstreams:
            id = downstream.get("id")
            # settings
            enabled = downstream.get("enabled")
            dest_ids = downstream.get("dest_ids")
            filters = downstream.get("filters")

            # state
            code = downstream.get("code", "none")
            error = downstream.get("error", "none")

            title = f"Agent Down {id}"
            if code == "error":
                status = error
            else:
                status = code

            page = widget.Page(widget.PageOptions(title))
            page_items = widget.PageItems()
            page_items.append(
                widget.PageItem(
                    "Status", status, widget.ListScreenValueColor.from_code(code)
                )
            )
            page_items.append(
                widget.PageItem(
                    "Enabled",
                    str(enabled),
                    widget.ListScreenValueColor.from_bool(enabled),
                )
            )

            # NOTE: display index 0 only
            if dest_ids:
                page_items.append(widget.PageItem(f"DestID", dest_ids[0]))

            if filters:
                filter_src_uuid = filters[0].get("src_edge_uuid", "")
                page_items.append(widget.PageItem(f"SrcEdgeUUID", filter_src_uuid))

                data_filters = filters[0].get("data_filters", {})
                if data_filters:
                    filter_data_type = data_filters[0].get("type", "")
                    filter_data_name = data_filters[0].get("name", "")
                    page_items.append(widget.PageItem(f"DataType", filter_data_type))
                    page_items.append(widget.PageItem(f"DataName", filter_data_name))

            agent_page_contents.append((page, page_items))

        if deferred_upload:
            # settings
            priority = deferred_upload.get("priority", "none")
            auto_delete = deferred_upload.get("auto_delete")
            auto_delete_threshold = deferred_upload.get("auto_delete_threshold")

            # state
            code = deferred_upload.get("code", "none")
            error = deferred_upload.get("error", "none")

            title = "Agent Deferred Upload"
            if code == "error":
                status = error
            else:
                status = code

            page = widget.Page(widget.PageOptions(title))
            page_items = widget.PageItems()
            page_items.append(
                widget.PageItem(
                    "Status",
                    status,
                    widget.ListScreenValueColor.from_code(
                        code, widget.ListScreenValueColorEnum.DARKGREY
                    ),
                )
            )
            page_items.append(widget.PageItem("Priority", priority))
            page_items.append(
                widget.PageItem(
                    "AutoDelete",
                    str(auto_delete),
                    widget.ListScreenValueColor.from_bool(auto_delete),
                )
            )
            page_items.append(
                widget.PageItem(
                    "Threshold", "{:.1f} GB".format(auto_delete_threshold / 1024)
                )
            )

            agent_page_contents.append((page, page_items))

        return agent_page_contents

    def _get_substitution_string(
        self, service_substitutions, substitution_variables, search_key, with_unit=True
    ) -> str:
        config_value = None
        default_value = None

        # search config value
        if service_substitutions:
            for service_substitution in service_substitutions:
                match = re.search(f"^{search_key}=(.*)", service_substitution)
                if match:
                    config_value = match.group(1)
                    break

        if config_value:
            value = config_value
        else:
            # search default value
            for substitution_variable in substitution_variables:
                variable_key = substitution_variable.get("key")
                if search_key == variable_key:
                    default = substitution_variable.get("default")
                    if default:
                        default_value = default
                    break

            if default_value:
                value = default_value
            else:
                return ""

        if with_unit:
            for substitution_variable in substitution_variables:
                variable_key = substitution_variable.get("key")
                if search_key == variable_key:
                    display_strings_i18n = substitution_variable.get(
                        "display_strings_i18n"
                    )
                    if display_strings_i18n:
                        # FIXME: support locale
                        unit = display_strings_i18n[0].get("unit", "")
                        if unit:
                            value = f"{value} {unit}"
                        break

        return value

    def _collect_service_specific_page_items(
        self, service_id, service_substitutions, substitution_variables
    ):
        service_specific_page_items: widget.PageItems = list()

        device_path = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_DEVICE_PATH"
        )
        input_send_rate = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_INPUT_SEND_RATE"
        )
        output_enabled = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_OUTPUT_ENABLED"
        )
        output_frequency = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_OUTPUT_FREQUENCY"
        )
        baudrate = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_BAUDRATE"
        )
        listenonly = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_LISTENONLY"
        )
        interface = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_INTERFACE"
        )
        fd = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_FD"
        )
        dbitrate = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_DBITRATE"
        )
        fps = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_FPS"
        )
        width = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_WIDTH", with_unit=False
        )
        height = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_HEIGHT", with_unit=False
        )
        bitrate = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_BITRATE"
        )
        audio_format = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_AUDIO_FORMAT"
        )
        audio_volume = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_AUDIO_VOLUME"
        )
        audio_boost = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_AUDIO_BOOST"
        )
        mixer_args = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_MIXER_ARGS"
        )
        high_nav_rate = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_HIGH_NAV_RATE"
        )
        send_interval = self._get_substitution_string(
            service_substitutions, substitution_variables, "DC_SEND_INTERVAL"
        )

        # NOTE: Currently, service identification is not implemented
        # so that it can be used for device connector services that will be added in the future.

        # NOTE: If more than 7 items are added, the page will display incorrectly.

        # Device Path
        if device_path:
            max_device_path_len = 17
            if len(device_path) > max_device_path_len:
                trim_index = len(device_path) - max_device_path_len
            else:
                trim_index = 0
            service_specific_page_items.append(
                widget.PageItem("Device", device_path[trim_index:])
            )
        if interface:
            service_specific_page_items.append(widget.PageItem("Interface", interface))

        # Analog
        if input_send_rate:
            service_specific_page_items.append(
                widget.PageItem("InFreq", input_send_rate)
            )
        if output_enabled:
            output_enabled = bool(strtobool(output_enabled))
            service_specific_page_items.append(
                widget.PageItem(
                    "Output",
                    str(output_enabled),
                    widget.ListScreenValueColor.from_bool(output_enabled),
                )
            )
        if output_frequency:
            service_specific_page_items.append(
                widget.PageItem("OutFreq", output_frequency)
            )

        # Camera
        if width and height:
            service_specific_page_items.append(
                widget.PageItem("Size", f"{width} x {height}")
            )
        if fps:
            service_specific_page_items.append(widget.PageItem("FPS", fps))

        # CAN / SocketCAN
        if listenonly:
            listenonly = bool(strtobool(listenonly))
            service_specific_page_items.append(
                widget.PageItem(
                    "ListenOnly",
                    str(listenonly),
                    widget.ListScreenValueColor.from_bool(listenonly),
                )
            )
        if fd:
            fd = bool(strtobool(fd))
            service_specific_page_items.append(
                widget.PageItem(
                    "FD",
                    str(fd),
                    widget.ListScreenValueColor.from_bool(fd),
                )
            )
        if baudrate:
            service_specific_page_items.append(widget.PageItem("Baudrate", baudrate))
        if bitrate:
            service_specific_page_items.append(widget.PageItem("Bitrate", bitrate))
        if dbitrate:
            service_specific_page_items.append(widget.PageItem("DataBitrate", dbitrate))

        # Audio
        if audio_format:
            service_specific_page_items.append(widget.PageItem("Format", audio_format))
        if audio_volume:
            service_specific_page_items.append(widget.PageItem("Volume", audio_volume))
        if audio_boost:
            service_specific_page_items.append(widget.PageItem("Boost", audio_boost))
        if mixer_args:
            service_specific_page_items.append(widget.PageItem("MixerArgs", mixer_args))

        # GPS
        if high_nav_rate:
            service_specific_page_items.append(
                widget.PageItem("HighNavRate", high_nav_rate)
            )

        # Device Inventory
        if send_interval:
            service_specific_page_items.append(
                widget.PageItem("SendInterval", send_interval)
            )

        return service_specific_page_items

    def _collect_device_connector_page_contents(self, api_response: ApiResponse):
        dc_page_contents: widget.PageContents = list()

        dcs = api_response.device_connectors()

        for dc in dcs:
            id = dc.get("id")
            service_id = dc.get("service_id")
            service_substitutions = dc.get("service_substitutions")
            substitution_variables = dc.get("substitution_variables")

            title = f"Device Connector {id}"
            page = widget.Page(widget.PageOptions(title))
            page_items = widget.PageItems()

            up_status = dc.get("upstream_ipc_state")
            if up_status:
                page_items.append(
                    widget.PageItem(
                        "Up Status",
                        up_status,
                        widget.ListScreenValueColor.from_code(up_status),
                    )
                )

            down_stats = dc.get("downstream_ipc_state")
            if down_stats:
                page_items.append(
                    widget.PageItem(
                        "Down Status",
                        down_stats,
                        widget.ListScreenValueColor.from_code(down_stats),
                    )
                )

            for page_item in self._collect_service_specific_page_items(
                service_id, service_substitutions, substitution_variables
            ):
                page_items.append(page_item)

            dc_page_contents.append((page, page_items))

        return dc_page_contents

    def _collect_hardware_info_page_contents(self, api_response: ApiResponse):
        hardware_info_page_contents: widget.PageContents = list()

        hardware_info = api_response.hardware_info()
        if not hardware_info:
            return hardware_info_page_contents

        hostname = hardware_info.get("hostname")
        cpu_usage = hardware_info.get("cpu_usage")
        load_average = hardware_info.get("load_average")
        disk_total = hardware_info.get("disk_total")
        disk_used = hardware_info.get("disk_used")
        memory_total = hardware_info.get("memory_total")
        memory_used = hardware_info.get("memory_used")
        version = hardware_info.get("version")

        page = widget.Page(widget.PageOptions("Hardware Info"))
        page_items = widget.PageItems()
        page_items.append(widget.PageItem("Name", hostname))
        page_items.append(widget.PageItem("CPU Usage", "{:.1f}%".format(cpu_usage)))
        page_items.append(
            widget.PageItem("Load Average", "{:.2f}".format(load_average))
        )
        if disk_total and disk_used:
            disk = (disk_used / disk_total) * 100.0
            disk_used = int(disk_used / (1024 * 1024 * 1024))
            disk_total = int(disk_total / (1024 * 1024 * 1024))
            page_items.append(
                widget.PageItem(
                    "Disk", "{:.1f}% ({}/{} GB)".format(disk, disk_used, disk_total)
                )
            )
        else:
            page_items.append(widget.PageItem("Disk", ""))
        if memory_total and memory_used:
            memory = (memory_used / memory_total) * 100.0
            page_items.append(
                widget.PageItem(
                    "Mem",
                    "{:.1f}% ({}/{} MB)".format(memory, memory_used, memory_total),
                )
            )
        else:
            page_items.append(widget.PageItem("Mem", ""))
        page_items.append(widget.PageItem("Version", version))

        hardware_info_page_contents.append((page, page_items))

        return hardware_info_page_contents

    def _set_beep_flags(self, main_screen_content, list_screen):
        if list_screen.is_error():
            self._beep_flag_error = True

        for icon in main_screen_content:
            if icon.type == widget.MainScreenIconType.MODE:
                if icon.value == widget.MainScreenIconValueMode.RECOVER_ON:
                    self._beep_flag_deferred_uploading = True
                else:
                    self._beep_flag_deferred_uploading = False

            if icon.type == widget.MainScreenIconType.QUEUE:
                if icon.value == widget.MainScreenIconValueQueue.SIZE_0B:
                    if self._queue_state == QueueState.SOME:
                        self._beep_flag_deferred_upload_complete = True
                        self._queue_state = QueueState.EMPTY
                elif icon.value != widget.MainScreenIconValueQueue.NONE:
                    self._queue_state = QueueState.SOME

    def _send_thread(self):
        logging.info("start send_thread()")

        self._cmd_sender.version()

        self._cmd_sender.init()

        logging.info("get api responses")
        api_response = ApiResponse(self._backend)
        api_response.update()

        # main screen
        main_screen = widget.MainScreen(self._cmd_sender)
        main_screen_content = self._collect_main_screen_content(api_response)
        main_screen.update(main_screen_content)

        # list screen
        list_screen = widget.ListScreen(self._cmd_sender)
        top_page = widget.Page(widget.PageOptions("Top"))
        list_screen.append_page(top_page, self._collect_top_page_items(api_response))
        for page, items in self._collect_network_page_contents(api_response):
            list_screen.append_page(page, items)
        for page, items in self._collect_agent_page_contents(api_response):
            list_screen.append_page(page, items)
        for page, items in self._collect_device_connector_page_contents(api_response):
            list_screen.append_page(page, items)
        for page, items in self._collect_hardware_info_page_contents(api_response):
            list_screen.append_page(page, items)
        list_screen.build()

        self._set_beep_flags(main_screen_content, list_screen)

        while True:
            api_response.update()

            main_screen_content = self._collect_main_screen_content(api_response)
            main_screen.update(main_screen_content)

            list_screen.update_page(
                top_page, self._collect_top_page_items(api_response)
            )
            for page, items in self._collect_network_page_contents(api_response):
                list_screen.update_page(page, items)
            for page, items in self._collect_agent_page_contents(api_response):
                list_screen.update_page(page, items)
            for page, items in self._collect_device_connector_page_contents(
                api_response
            ):
                list_screen.update_page(page, items)
            for page, items in self._collect_hardware_info_page_contents(api_response):
                list_screen.update_page(page, items)
            list_screen.delete_unupdated_page_items()

            self._set_beep_flags(main_screen_content, list_screen)

    def _recv_thread(self):
        config = self._config

        logging.info("Start recv_thread()")

        # Config setting
        store_volume_config = False
        section = "m5stack"

        while True:
            data = self._cmd_receiver.readline()
            try:
                data_str = data.decode()
                logging.debug("[READ ]: {}".format(data_str))
            except UnicodeDecodeError:
                logging.error("detect UnicodeDecodeError. Skip")

            # checking ACK responce
            if data == b'"ack"\r\n':
                self._cmd_sender.receive_ok()
            elif data == b'"recovery":"1"\r\n':
                logging.info("detect recovery on")
                self._recover_flg = True
            elif data == b'"meas":"0"\r\n':
                logging.info("detect meas command")
                self._restart_service_flg = True
            elif data == b'"volume":"3"\r\n':
                logging.info("detect volume 3")
                config.set(section, "volume", "3")
                store_volume_config = True
            elif data == b'"volume":"2"\r\n':
                logging.info("detect volume 2")
                config.set(section, "volume", "2")
                store_volume_config = True
            elif data == b'"volume":"1"\r\n':
                logging.info("detect volume 1")
                config.set(section, "volume", "1")
                store_volume_config = True
            elif data == b'"volume":"0"\r\n':
                logging.info("detect volume 0")
                config.set(section, "volume", "0")
                store_volume_config = True

            # generate firmware version file
            match = re.search(r'"version":"(.*)"', data_str)
            if match:
                firmware_version = match.group(1) + "\n"
                logging.info(f"FW version = {firmware_version}")
                try:
                    with open(FW_VERSION_FILE_PATH, "w") as f:
                        f.write(firmware_version)
                except:
                    logging.error(
                        "Error: Could not write to fw_version file:"
                        + FW_VERSION_FILE_PATH
                    )

            if store_volume_config:
                try:
                    config.write(open(self._config_file, "w"))
                except:
                    logging.error(
                        "Error: Could not write to config file:" + self._config_file
                    )
                store_volume_config = False

    def _api_thread(self):
        logging.info("Start api_thread()")
        while True:
            if self._recover_flg:
                logging.info("stop agent streamer")
                success = self._backend.post("stop_agent_streamer")
                if success:
                    self._cmd_sender.beep(3, 50, 1)
                else:
                    self._cmd_sender.beep(3, 50, 2)
                logging.info(f"stop agent streamer is done. success = {success}")
                self._recover_flg = False
            elif self._restart_service_flg:
                logging.info("restart agent streamer")
                stop_success = self._backend.post("stop_agent_streamer")
                start_success = self._backend.post("start_agent_streamer")
                if stop_success and start_success:
                    self._cmd_sender.beep(3, 50, 1)
                else:
                    self._cmd_sender.beep(3, 50, 2)
                logging.info(
                    f"restart agent streamer is done. stop_success = {stop_success}, start_success = {start_success}"
                )
                self._restart_service_flg = False
            else:
                time.sleep(0.5)

    def run(self):
        for th in self._th_list:
            th.start()

        self._send_thread()


def main(config_file):
    tdc = TerminalDisplayClient(config_file)
    tdc.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT_INFO)

    parser = OptionParser(
        usage="sudo %prog [-f config file]", version="%prog ver " + __version__
    )
    parser.add_option(
        "-f", "--file", dest="filename", help="config file", metavar="FILE"
    )
    parser.print_version()

    (options, args) = parser.parse_args()
    if options.filename is None:
        config_file = DEFAULT_CONFIG_FILE
    else:
        logging.info("detect config file option")
        config_file = options.filename

    main(config_file)
