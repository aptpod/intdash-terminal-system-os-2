#!/usr/bin/env python3
# coding: utf-8

import argparse
from datetime import datetime
import re
import requests
import socket
import urllib


class TerminalDisplayBackend:
    def __init__(self, api_client):
        self.api_client = api_client

    def __del__(self):
        None

    def get_connection(self):
        """intdash Agentとintdashサーバー間の接続に関する設定を取得します。

        Returns
        -------
        obj
            Get Connection Settings のレスポンス
            /agent/connection

        bool
            OK
        """

        resp = self.api_client.get_connection()
        if resp.status_code != 200:
            return {}, False
        connection = resp.json()

        return connection, True

    def get_stream(self):
        """intdash Agent Streamerの全てのストリームを包括したステータスを取得します。

        Returns
        -------
        obj
            ストリームのステータス

            * **auto_start** (*bool*)
                true の場合、Terminal Systemを起動すると自動的にサービスが起動します。

            * **state** (*str*)
                現在から５秒以内のストリームの状態を示す文字列。

                * connected - intdashサーバーと接続されています。
                * disconnected - intdashサーバーと接続されていません
                * none - 起動していません

            * **update_time** (*datetime or None*)
                最終更新タイムスタンプ

        bool
            OK
        """

        resp = self.api_client.list_upstream_state()
        if resp.status_code != 200:
            return {}, False
        ups_status = resp.json()

        resp = self.api_client.list_downstream_state()
        if resp.status_code != 200:
            return {}, False
        downs_status = resp.json()

        state, update_time = self._aggregate_state(ups_status + downs_status)
        if state == "quiet":
            state = "connected"

        auto_start = self._is_measurement_auto_start()

        return {
            "auto_start": auto_start,
            "state": state,
            "update_time": update_time,
        }, True

    def get_upstreams(self):
        """intdash Agent Streamerのupstream設定およびステータスのリストを取得します。

        Returns
        -------
        obj
            upstream設定およびステータスのリスト
            /agent/upstreams と/agent/upstreams/-/state を統合したもの

        bool
            OK
        """
        resp = self.api_client.list_upstream()
        if resp.status_code != 200:
            return {}, False
        ups = resp.json()

        resp = self.api_client.list_upstream_state()
        if resp.status_code != 200:
            return {}, False
        ups_states = resp.json()

        for state in ups_states:
            up = [up for up in ups if state["id"] == up["id"]][0]
            up.update(state)

        return ups, True

    def get_downstreams(self):
        """intdash Agent Streamerのdownstream設定およびステータスのリストを取得します。

        Returns
        -------
        obj
            downstream設定およびステータスのリスト
            /agent/downstreams と/agent/downstreams/-/state を統合したもの

        bool
            OK
        """
        resp = self.api_client.list_downstream()
        if resp.status_code != 200:
            return {}, False
        downs = resp.json()

        resp = self.api_client.list_downstream_state()
        if resp.status_code != 200:
            return {}, False
        downs_states = resp.json()

        for state in downs_states:
            down = [down for down in downs if state["id"] == down["id"]][0]
            down.update(state)

        return downs, True

    def get_deferred_upload(self):
        """intdash Agent Deferred Upload設定およびステータスを取得します。

        Returns
        -------
        obj
            deferred_upload設定およびステータスのリスト
            /agent/deferred_upload と/agent/deferred_upload/state を統合したもの

        bool
            OK
        """

        resp = self.api_client.get_deferred_upload()
        if resp.status_code != 200:
            return {}, False
        deferred_upload = resp.json()

        resp = self.api_client.get_deferred_upload_state()
        if resp.status_code != 200:
            return {}, False
        deferred_upload_state = resp.json()

        deferred_upload.update(deferred_upload_state)

        return deferred_upload, True

    def enable_auto_start(self):
        """電源Onに連動した自動起動設定を有効にします。

        Returns
        -------
        bool
            自動起動設定を有効にしました。
        """
        resp = self.api_client.patch_compose_measurement(True)
        return resp.status_code == 200

    def disable_auto_start(self):
        """電源Onに連動した自動起動設定を無効にします。

        Returns
        -------
        bool
            自動起動設定を無効にしました。
        """
        resp = self.api_client.patch_compose_measurement(False)
        return resp.status_code == 200

    def start_agent_streamer(self):
        """計測を開始します。

        Returns
        -------
        bool
            計測を開始しました。
        """
        resp = self.api_client.start_compose_measurement()
        return resp.status_code == 204

    def stop_agent_streamer(self):
        """計測を停止します。

        Returns
        -------
        bool
            計測を停止しました。
        """
        resp = self.api_client.stop_compose_measurement()
        return resp.status_code == 204

    def get_daemon_state(self):
        """intdash Agent Daemonのステータスを取得します。

        Returns
        -------
        obj
            Daemonのステータス

            * **state** (*str*)
                現在から５秒以内のストリームの状態を示す文字列。

                * connected - intdashサーバーと接続されています。
                * disconnected - intdashサーバーと接続されていません
                * none - 起動していません

            * **pending_data_size** (*int*)
                送信待ちデータサイズ（バイト）

            * **average_uploading_speed** (*int*)
                遅延アップロードの平均アップロード速度（バイト／秒）

            * **update_time** (*datetime or None*)
                最終更新タイムスタンプ

        bool
            OK
        """

        resp = self.api_client.get_deferred_upload_state()
        if resp.status_code != 200:
            return {}, False
        status = [resp.json()]

        state, update_time = self._aggregate_state(status)
        if state == "quiet":
            state = "connected"

        resp = self.api_client.list_measurements()
        if resp.status_code != 200:
            return {}, False
        measurements = resp.json()

        pending_data_size = self._aggregate_pending_data_size(measurements)

        average_uploading_speed = 0
        bitrate = status[0].get("bitrate")
        if bitrate is not None:
            average_uploading_speed = round(bitrate / 8, 2)

        return {
            "state": state,
            "pending_data_size": pending_data_size,
            "average_uploading_speed": average_uploading_speed,
            "update_time": update_time,
        }, True

    def get_device_connectors(self):
        """Device Connector 設定およびステータスを取得します。

        Returns
        -------
        obj
            /device_connectors のレスポンスに以下を統合
            * デバイスコネクターIPCの統合ステータス(upstream_ipc_state, downstream_ipc_state)
                * /agent/device_connectors_upstream/-/state
                * /agent/device_connectors_downstream/-/state
            * service_id の substitution_variables
                * /device_connector_services

        bool
            OK
        """

        resp = self.api_client.list_device_connectors()
        if resp.status_code != 200:
            return {}, False
        dcs = resp.json()

        resp = self.api_client.list_device_connector_state_for_upstream()
        if resp.status_code != 200:
            return {}, False
        dc_up_states = resp.json()

        resp = self.api_client.list_device_connector_state_for_downstream()
        if resp.status_code != 200:
            return {}, False
        dc_down_states = resp.json()

        resp = self.api_client.list_device_connector_services()
        if resp.status_code != 200:
            return {}, False
        dc_services = resp.json()

        for dc in dcs:
            up_ipc_ids = dc["upstream_ipc_ids"]
            down_ipc_ids = dc["downstream_ipc_ids"]

            if up_ipc_ids:
                up_states = self._filter_state_by_ids(up_ipc_ids, dc_up_states)
                up_state, _ = self._aggregate_state(up_states)
                dc["upstream_ipc_state"] = up_state

            if down_ipc_ids:
                down_states = self._filter_state_by_ids(down_ipc_ids, dc_down_states)
                down_state, _ = self._aggregate_state(down_states)
                dc["downstream_ipc_state"] = down_state

            dc_service = [
                d for d in dc_services if d["service_id"] == dc["service_id"]
            ][0]
            dc["substitution_variables"] = dc_service["substitution_variables"]

        return dcs, True

    def get_device_connector_gps_state(self):
        """全てのGPSのデバイスコネクターを包括したステータスを取得します。

        Returns
        -------
        obj
            GPSのデバイスコネクターのステータス

            * **state** (*str*)
                現在から５秒以内のストリームの状態を示す文字列。

                * connected - intdashサーバーと接続されています。
                * quiet - intdashサーバーと接続されていますが、データを送信していません。
                * disconnected - intdashサーバーと接続されていません。
                * none - 起動していません。

            * **quality** (*str*)
                * no_fix
                * dead_reckoning_only
                * 2d_fix
                * 3d_fix
                * gps_+_dead_reckoning
                * time_only_fix
                * none - 起動していません。

            * **detail_urls** (*list of str*)
                デバイスコネクターの詳細情報を取得するためのTerminal System API のエンドポイント。

            * **update_time** (*datetime or None*)
                最終更新タイムスタンプ

        bool
            OK
        """
        qualities_ubx = {
            0: {"description": "no_fix", "priority": 1},
            1: {"description": "dead_reckoning_only", "priority": 3},
            2: {"description": "2d_fix", "priority": 4},
            3: {"description": "3d_fix", "priority": 5},
            4: {"description": "gps_+_dead_reckoning", "priority": 6},
            5: {"description": "time_only_fix", "priority": 2},
        }
        qualities_nmea = {
            "no fix": {"description": "no_fix", "priority": 1},
            "2D fix": {"description": "2d_fix", "priority": 4},
            "3D fix": {"description": "3d_fix", "priority": 5},
        }
        quality = {"description": "none", "priority": 0}

        ret, ok = self._list_device_connectors_state("GPS")
        if ok == False:
            return {}, False
        else:
            (up_states, _, up_urls, _) = ret

        state, update_time = self._aggregate_state(up_states)

        if state != "none":
            resp = self.api_client.get_terminal_system_metrics()
            if resp.status_code != 200:
                return {}, False
            metrics = resp.json()

            gpx_fix_ubx = (
                metrics.get("gps", {})
                .get("UBX-HNR-PVT", {})
                .get("gpsFix", {})
                .get("value")
            )
            quality_ubx = qualities_ubx.get(gpx_fix_ubx)

            gps_fix_nmea = metrics.get("gps", {}).get("nmea", {}).get("fix")
            quality_nmea = qualities_nmea.get(gps_fix_nmea)

            if quality_ubx and quality_nmea:
                quality = (
                    quality_ubx
                    if quality_ubx["priority"] < quality_nmea["priority"]
                    else quality_nmea
                )
            elif quality_ubx:
                quality = quality_ubx
            elif quality_nmea:
                quality = quality_nmea

        return {
            "state": state,
            "quality": quality.get("description", "none"),
            "detail_urls": up_urls,
            "update_time": update_time,
        }, True

    def get_device_connector_can_state(self):
        """全てのCANのデバイスコネクターを包括したステータスを取得します。

        Returns
        -------
        obj
            CANのデバイスコネクターのステータス

            * **state** (*str*)
                現在から５秒以内のストリームの状態を示す文字列。

                * connected - intdashサーバーと接続されています。
                * quiet - intdashサーバーと接続されていますが、データを送信していません。
                * disconnected - intdashサーバーと接続されていません。
                * none - 起動していません。

            * **detail_urls** (*list of str*)
                デバイスコネクターの詳細情報を取得するためのTerminal System API のエンドポイント。

            * **update_time** (*datetime or None*)
                最終更新タイムスタンプ

        bool
            OK
        """

        ret, ok = self._list_device_connectors_state("CAN")
        if ok == False:
            return {}, False
        else:
            (up_states, down_states, up_urls, down_urls) = ret

        state, update_time = self._aggregate_state(up_states + down_states)

        return {
            "state": state,
            "detail_urls": up_urls + down_urls,
            "update_time": update_time,
        }, True

    def get_device_connector_camera_state(self):
        """全てのCameraのデバイスコネクターを包括したステータスを取得します。

        Returns
        -------
        obj
            Cameraのデバイスコネクターのステータス

            * **state** (*str*)
                現在から５秒以内のストリームの状態を示す文字列。

                * connected - intdashサーバーと接続されています。
                * quiet - intdashサーバーと接続されていますが、データを送信していません。
                * disconnected - intdashサーバーと接続されていません。
                * none - 起動していません。

            * **detail_urls** (*list of str*)
                デバイスコネクターの詳細情報を取得するためのTerminal System API のエンドポイント。

            * **update_time** (*datetime or None*)
                最終更新タイムスタンプ

        bool
            OK
        """

        ret, ok = self._list_device_connectors_state("Camera")
        if ok == False:
            return {}, False
        else:
            (up_states, _, up_urls, _) = ret

        state, update_time = self._aggregate_state(up_states)

        return {
            "state": state,
            "detail_urls": up_urls,
            "update_time": update_time,
        }, True

    def get_device_connector_other_state(self):
        """全てのその他のデバイスコネクターを包括したステータスを取得します。

        Returns
        -------
        obj
            デバイスコネクターのステータス

            * **state** (*str*)
                現在から５秒以内のストリームの状態を示す文字列。

                * connected - intdashサーバーと接続されています。
                * quiet - intdashサーバーと接続されていますが、データを送信していません。
                * disconnected - intdashサーバーと接続されていません。
                * none - 起動していません。

            * **detail_urls** (*list of str*)
                デバイスコネクターの詳細情報を取得するためのTerminal System API のエンドポイント。

            * **update_time** (*datetime or None*)
                最終更新タイムスタンプ

        bool
            OK
        """

        ret, ok = self._list_device_connectors_state("")
        if ok == False:
            return {}, False
        else:
            (up_states, down_states, up_urls, down_urls) = ret

        state, update_time = self._aggregate_state(up_states + down_states)

        return {
            "state": state,
            "detail_urls": up_urls + down_urls,
            "update_time": update_time,
        }, True

    def _get_current_device(self, devices):
        resp = self.api_client.get_connection()
        if resp.status_code != 200:
            return {}
        connection = resp.json()
        server_url = connection["server_url"]
        hostname = server_url.split("//")[-1].split("/")[0]
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            ip = "8.8.8.8"

        resp = self.api_client.get_network_route(ip)
        if resp.status_code != 200:
            return {}
        route = resp.json()
        nic_name = route["nic_name"]

        device = [d for d in devices if d.get("nic_name") == nic_name]
        return device[0] if device else {}

    def _get_carrier(self, metrics):
        carrier = "none"
        mmcli = metrics.get("mmcli", {})
        if len(mmcli) > 0:
            operator_name = (
                mmcli[0].get("sim", {}).get("properties", {}).get("operator-name")
            )
            carrier = operator_name if operator_name else carrier
        return carrier

    def _get_rssi(self, metrics):
        rssi = 0
        mmcli = metrics.get("mmcli", {})
        if len(mmcli) > 0:
            rssi = mmcli[0].get("signal", {}).get("lte", {}).get("rssi")
            try:
                rssi = int(float(rssi))
            except:
                rssi = 0
        return rssi

    def _get_mode(self, metrics):
        mode = "none"
        mmcli = metrics.get("mmcli", {})
        if len(mmcli) > 0:
            current_modes = mmcli[0].get("generic", {}).get("current-modes")
            if current_modes:
                match = re.search(r"preferred:\s*(\w+)", str(current_modes))
                mode = match.group(1) if match else mode
        return mode

    def get_network_state(self):
        """ネットワークのステータスを取得します。

        Returns
        -------
        obj
            ネットワークのステータス

            * **current_device** (*dict*)
                現在使用している Network Device。 取得できない場合は空の辞書を返します。

            * **gsm_state.carrier** (*str")
                接続中のキャリア名。取得できない場合は "none" を返します。

            * **gsm_state.rssi** (*int")
                RSSI。取得できない場合は0を返します。

            * **gsm_state.mode** (*str")
                接続中のモード。取得できない場合は "none" を返します。

            * **devices** (*list of dict*)
                Network Deviceのリスト

            * **connections** (*list of dict*)
                Network Connectionのリスト

            * **update_time** (*datetime or None*)
                最終更新タイムスタンプ

        bool
            OK
        """
        resp = self.api_client.get_network_devices()
        if resp.status_code != 200:
            return {}, False
        devices = resp.json()

        current_device = self._get_current_device(devices)

        resp = self.api_client.get_terminal_system_metrics()
        if resp.status_code != 200:
            return 0
        metrics = resp.json()

        carrier = self._get_carrier(metrics)
        rssi = self._get_rssi(metrics)
        mode = self._get_mode(metrics)

        resp = self.api_client.get_network_connections()
        if resp.status_code != 200:
            return {}, False
        connections = resp.json()

        return {
            "current_device": current_device,
            "gsm_state": {
                "carrier": carrier,
                "rssi": rssi,
                "mode": mode,
            },
            "devices": devices,
            "connections": connections,
            "update_time": datetime.now(),
        }, True

    def get_hardware_info(self):
        """ハードウェア情報を取得します。

        Returns
        -------
        obj
            統計情報

            * **hostname** (*str*)
                Terminal Systemのホスト名

            * **cpu_usage** (*float*)
                CPU使用率（％）

            * **load_average** (*float*)
                ロードアベレージ

            * **disk_total** (*int*)
                データ保存ディスクの容量（Byte）

            * **disk_used** (*int*)
                データ保存ディスクの使用量（Byte）

            * **memory_total** (*int*)
                メモリ容量（MB）

            * **memory_used** (*int*)
                メモリ使用量（MB）

            * **version** (*str*)
                Terminal Systemのバージョン

        bool
            OK
        """

        resp = self.api_client.get_terminal_system()
        if resp.status_code != 200:
            return {}, False
        terminal_system = resp.json()

        resp = self.api_client.get_terminal_system_identification()
        if resp.status_code != 200:
            return {}, False
        terminal_system_identification = resp.json()

        hostname = terminal_system_identification["computer_name"]
        version = terminal_system["os_version"]

        resp = self.api_client.get_terminal_system_metrics()
        if resp.status_code != 200:
            return {}, False
        metrics = resp.json()

        top = metrics.get("top")
        if top:
            cpu_usage = round(100.0 - (top[0]["cpu_idle"] + top[0]["cpu_wait"]), 2)
            load_average = round(top[0]["load_1m"], 2)
            disk_total = metrics["data_partition"]["total"]
            disk_used = round(disk_total - metrics["data_partition"]["available"])
            memory_total = round(top[0]["mem_total"])
            memory_used = round(top[0]["mem_used"])
        else:
            return {}, False

        return {
            "hostname": hostname,
            "cpu_usage": cpu_usage,
            "load_average": load_average,
            "disk_total": disk_total,
            "disk_used": disk_used,
            "memory_total": memory_total,
            "memory_used": memory_used,
            "version": version,
        }, True

    def get_events(self, level="WARN"):
        """エラーイベントのリストを取得します。

        Returns
        -------
        list of obj
            エラーイベントのリスト

            * *obj*
                * **description** (*str*)
                    イベントの内容

                * **level** (*str*)
                    * FATAL
                    * ERROR
                    * WARN
                    * INFO
                    * DEBUG
                    * TRACE

                * **create_time** (*str*)
                    作成時刻（RFC3339）

        bool
            OK
        """

        level_dict = {
            "TRACE": 1,
            "DEBUG": 2,
            "INFO": 3,
            "WARN": 4,
            "ERROR": 5,
            "FATAL": 6,
        }
        th = level_dict[level]

        resp = self.api_client.list_events()
        if resp.status_code != 200:
            return {}, False
        events = resp.json()

        filtered_events = list([x for x in events if level_dict[x["level"]] >= th])
        return filtered_events

    def _list_device_connectors_state(self, pattern):
        dcs_resp = self.api_client.list_device_connectors()
        if dcs_resp.status_code != 200:
            return (), False
        dcs = self._filter_device_connectors_by_service_id(pattern, dcs_resp.json())

        up_ipc_ids = []
        down_ipc_ids = []
        for dc in dcs:
            up_ipc_ids += dc["upstream_ipc_ids"]
            down_ipc_ids += dc["downstream_ipc_ids"]

        if not up_ipc_ids:
            up_states = []
        else:
            st_resp = self.api_client.list_device_connector_state_for_upstream()
            if st_resp.status_code != 200:
                return (), False
            up_states = self._filter_state_by_ids(up_ipc_ids, st_resp.json())

        if not down_ipc_ids:
            down_states = []
        else:
            st_resp = self.api_client.list_device_connector_state_for_downstream()
            if st_resp.status_code != 200:
                return (), False
            down_states = self._filter_state_by_ids(down_ipc_ids, st_resp.json())

        up_urls = list(
            [
                self.api_client.base_url + "/agent/device_connectors_upstream/" + x
                for x in up_ipc_ids
                if x
            ]
        )
        down_urls = list(
            [
                self.api_client.base_url + "/agent/device_connectors_downstream/" + x
                for x in down_ipc_ids
                if x
            ]
        )

        return (up_states, down_states, up_urls, down_urls), True

    def _aggregate_state(self, states: list):
        aggregate_state = "none"
        update_time = None

        found_connected = False
        found_quiet = False
        found_disconnected_or_error = False

        for state in states:
            code = state.get("code")
            if code is None:
                continue

            if code == "connected":
                found_connected = True
            elif code == "quiet":
                found_quiet = True
            elif code == "disconnected" or code == "error":
                found_disconnected_or_error = True

            ts = state.get("update_time")
            ts = self._utc_rfc3339_to_datetime(ts)
            if ts is None:
                continue
            if update_time is None or update_time < ts:
                update_time = ts

        """
        ----------------------------+-------------------------------------------
        found_disconnected_or_error | True          | False | False     | False
        found_connected             | *             | False | True      | *
        found_quiet                 | *             | False | False     | True
        ----------------------------+-------------------------------------------
        aggregate_state             | disconnected  | none  | connected | quiet
        """

        if found_disconnected_or_error:
            aggregate_state = "disconnected"
        else:
            if found_quiet:
                aggregate_state = "quiet"
            elif found_connected:
                aggregate_state = "connected"

        return aggregate_state, update_time

    def _aggregate_pending_data_size(self, measurements):
        pending_data_size = 0

        for stream in measurements:
            size = stream.get("pending_data_size")
            pending_data_size += size

        return pending_data_size

    def _filter_device_connectors_by_service_id(self, pattern, device_connectors):
        return [d for d in device_connectors if re.search(pattern, d["service_id"])]

    def _filter_state_by_ids(self, ipc_ids, status):
        return [x for x in status if ipc_ids.count(x["id"])]

    def _utc_rfc3339_to_datetime(self, utc_rfc3339):
        dt = None
        try:
            dt = datetime.strptime(str(utc_rfc3339), "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            pass
        return dt

    def _is_measurement_auto_start(self):
        compose = self.api_client.get_compose_measurement().json()
        return compose.get("boot_after") == "system"


class TerminalSystemAPIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_terminal_system(self):
        return requests.get(self.base_url + "/terminal_system")

    def get_terminal_system_identification(self):
        return requests.get(self.base_url + "/terminal_system/identification")

    def get_network_route(self, ip):
        return requests.get(self.base_url + "/network/route/" + ip)

    def get_network_devices(self):
        return requests.get(self.base_url + "/network_devices")

    def get_network_connections(self):
        return requests.get(self.base_url + "/network_connections")

    def get_terminal_system_metrics(self):
        return requests.get(self.base_url + "/terminal_system/metrics")

    def get_connection(self):
        return requests.get(self.base_url + "/agent/connection")

    def list_upstream(self):
        return requests.get(self.base_url + "/agent/upstreams")

    def list_upstream_state(self):
        params = {"enabled": "true"}
        return requests.get(self.base_url + "/agent/upstreams/-/state", params=params)

    def list_downstream(self):
        return requests.get(self.base_url + "/agent/downstreams")

    def list_downstream_state(self):
        params = {"enabled": "true"}
        return requests.get(self.base_url + "/agent/downstreams/-/state", params=params)

    def get_deferred_upload(self):
        return requests.get(self.base_url + "/agent/deferred_upload")

    def get_deferred_upload_state(self):
        return requests.get(self.base_url + "/agent/deferred_upload/state")

    def list_measurements(self):
        return requests.get(self.base_url + "/agent/measurements")

    def list_device_connectors_for_upstream(self):
        return requests.get(self.base_url + "/agent/device_connectors_upstream")

    def list_device_connector_state_for_upstream(self):
        params = {"enabled": "true"}
        return requests.get(
            self.base_url + "/agent/device_connectors_upstream/-/state", params=params
        )

    def list_device_connectors_for_downstream(self):
        return requests.get(self.base_url + "/agent/device_connectors_downstream")

    def list_device_connector_state_for_downstream(self):
        params = {"enabled": "true"}
        return requests.get(
            self.base_url + "/agent/device_connectors_downstream/-/state", params=params
        )

    def list_device_connectors(self):
        return requests.get(self.base_url + "/device_connectors")

    def list_device_connector_services(self):
        return requests.get(self.base_url + "/device_connector_services")

    def list_events(self):
        return requests.get(self.base_url + "/events")

    def get_compose_measurement(self):
        return requests.get(self.base_url + "/docker/composes/measurement")

    def patch_compose_measurement(self, auto_start: bool):
        headers = {"Content-Type": "application/json"}
        data = '{{"boot_after":"{0}"}}'.format("system" if auto_start else "")
        return requests.patch(
            self.base_url + "/docker/composes/measurement", headers=headers, data=data
        )

    def start_compose_measurement(self):
        return requests.post(self.base_url + "/docker/composes/measurement/start")

    def stop_compose_measurement(self):
        return requests.post(self.base_url + "/docker/composes/measurement/stop")


if __name__ == "__main__":
    backend = TerminalDisplayBackend(
        TerminalSystemAPIClient("http://localhost:8081/api")
    )

    parser = argparse.ArgumentParser(
        description="Terminal System API wrapper for Terminal Display"
    )
    subparsers = parser.add_subparsers()
    subparsers.add_parser("get_stream").set_defaults(
        sub_cmd=lambda _: print(backend.get_stream())
    )
    subparsers.add_parser("enable_auto_start").set_defaults(
        sub_cmd=lambda _: print(backend.enable_auto_start())
    )
    subparsers.add_parser("disable_auto_start").set_defaults(
        sub_cmd=lambda _: print(backend.disable_auto_start())
    )
    subparsers.add_parser("start_agent_streamer").set_defaults(
        sub_cmd=lambda _: print(backend.start_agent_streamer())
    )
    subparsers.add_parser("stop_agent_streamer").set_defaults(
        sub_cmd=lambda _: print(backend.stop_agent_streamer())
    )
    subparsers.add_parser("get_daemon_state").set_defaults(
        sub_cmd=lambda _: print(backend.get_daemon_state())
    )
    subparsers.add_parser("get_device_connector_gps_state").set_defaults(
        sub_cmd=lambda _: print(backend.get_device_connector_gps_state())
    )
    subparsers.add_parser("get_device_connector_can_state").set_defaults(
        sub_cmd=lambda _: print(backend.get_device_connector_can_state())
    )
    subparsers.add_parser("get_device_connector_can_state").set_defaults(
        sub_cmd=lambda _: print(backend.get_device_connector_can_state())
    )
    subparsers.add_parser("get_device_connector_camera_state").set_defaults(
        sub_cmd=lambda _: print(backend.get_device_connector_camera_state())
    )
    subparsers.add_parser("get_device_connector_other_state").set_defaults(
        sub_cmd=lambda _: print(backend.get_device_connector_other_state())
    )
    subparsers.add_parser("get_network_state").set_defaults(
        sub_cmd=lambda _: print(backend.get_network_state())
    )
    subparsers.add_parser("get_hardware_info").set_defaults(
        sub_cmd=lambda _: print(backend.get_hardware_info())
    )
    sub = subparsers.add_parser("get_events")
    sub.add_argument(
        "-l",
        "--level",
        default="WARN",
        help="event level (TRACE|DEBUG|INFO|WARN|ERROR|FATAL)",
    )
    sub.set_defaults(sub_cmd=lambda args: print(backend.get_events(args.level)))

    args = parser.parse_args()
    if hasattr(args, "sub_cmd"):
        args.sub_cmd(args)
    else:
        parser.print_help()
