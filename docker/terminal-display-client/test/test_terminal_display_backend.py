from datetime import datetime
import requests
import tempfile
import terminal_display_backend as bk
import unittest


class MockTerminalSystemAPIClient:
    def __init__(self, responses):
        self.base_url = ""
        self.__responses = responses

    def list_upstream_state(self):
        return self.__responses["list_upstream_state"]

    def list_downstream_state(self):
        return self.__responses["list_downstream_state"]

    def get_compose_measurement(self):
        return self.__responses["get_compose_measurement"]

    def list_device_connectors_for_upstream(self):
        return self.__responses["list_device_connectors_for_upstream"]

    def list_device_connector_state_for_upstream(self):
        return self.__responses["list_device_connector_state_for_upstream"]

    def list_device_connectors_for_downstream(self):
        return self.__responses["list_device_connectors_for_downstream"]

    def list_device_connector_state_for_downstream(self):
        return self.__responses["list_device_connector_state_for_downstream"]

    def list_device_connectors(self):
        return self.__responses["list_device_connectors"]

    def list_device_connector_services(self):
        return self.__responses["list_device_connector_services"]

    def list_events(self):
        return self.__responses["list_events"]


class TestTerminalDisplayBackend(unittest.TestCase):
    def test_get_stream(self):
        tests = [
            {
                "responses": {
                    "list_upstream_state": self.__new_response(
                        200,
                        """[
                        {}
                    ]""",
                    ),
                    "list_downstream_state": self.__new_response(
                        200,
                        """[
                        {"code":"none","update_time":"2000-01-01T00:00:01Z"}
                    ]""",
                    ),
                    "get_compose_measurement": self.__new_response(200, "{}"),
                },
                "expect": (
                    {
                        "auto_start": False,
                        "state": "none",
                        "update_time": datetime(2000, 1, 1, 0, 0, 1),
                    },
                    True,
                ),
            },
            {
                "responses": {
                    "list_upstream_state": self.__new_response(
                        200,
                        """[
                        {"code":"quiet","update_time":"2000-01-01T00:00:01Z"}
                    ]""",
                    ),
                    "list_downstream_state": self.__new_response(
                        200,
                        """[
                        {"code":"disconnected","update_time":"2000-01-01T00:00:00Z"}
                    ]""",
                    ),
                    "get_compose_measurement": self.__new_response(200, "{}"),
                },
                "expect": (
                    {
                        "auto_start": False,
                        "state": "disconnected",
                        "update_time": datetime(2000, 1, 1, 0, 0, 1),
                    },
                    True,
                ),
            },
            {
                "responses": {
                    "list_upstream_state": self.__new_response(200, "[]"),
                    "list_downstream_state": self.__new_response(200, "[]"),
                    "get_compose_measurement": self.__new_response(
                        200, '{"boot_after":"system"}'
                    ),
                },
                "expect": (
                    {"auto_start": True, "state": "none", "update_time": None},
                    True,
                ),
            },
            {
                "responses": {
                    "list_upstream_state": self.__new_response(200, "[]"),
                    "list_downstream_state": self.__new_response(200, "[]"),
                    "get_compose_measurement": self.__new_response(
                        200, '{"boot_after":"measurement"}'
                    ),
                },
                "expect": (
                    {"auto_start": False, "state": "none", "update_time": None},
                    True,
                ),
            },
            {
                "responses": {
                    "list_upstream_state": self.__new_response(500, "[]"),
                    "list_downstream_state": self.__new_response(200, "[]"),
                    "get_compose_measurement": self.__new_response(200, "{}"),
                },
                "expect": ({}, False),
            },
            {
                "responses": {
                    "list_upstream_state": self.__new_response(200, "[]"),
                    "list_downstream_state": self.__new_response(500, "[]"),
                    "get_compose_measurement": self.__new_response(200, "{}"),
                },
                "expect": ({}, False),
            },
            {
                "responses": {
                    "list_upstream_state": self.__new_response(200, "[]"),
                    "list_downstream_state": self.__new_response(200, "[]"),
                    "get_compose_measurement": self.__new_response(500, "{}"),
                },
                "expect": (
                    {"auto_start": False, "state": "none", "update_time": None},
                    True,
                ),
            },
        ]

        for test in tests:
            backend = bk.TerminalDisplayBackend(
                MockTerminalSystemAPIClient(test["responses"])
            )
            actual = backend.get_stream()
            self.assertEqual(actual, test["expect"])

    def test_get_events(self):
        tests = [
            {
                "responses": {
                    "list_events": self.__new_response(
                        200,
                        """[
                            {"description": "fatal", "level": "FATAL", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "error", "level": "ERROR", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "warn", "level": "WARN", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "info", "level": "INFO", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "debug", "level": "DEBUG", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "trace", "level": "TRACE", "create_time": "2000-01-01T00:00:00Z"}
                        ]""",
                    ),
                },
                "levels": None,
                "expect": [
                    {
                        "description": "fatal",
                        "level": "FATAL",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                    {
                        "description": "error",
                        "level": "ERROR",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                    {
                        "description": "warn",
                        "level": "WARN",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                ],
            },
            {
                "responses": {
                    "list_events": self.__new_response(
                        200,
                        """[
                            {"description": "fatal", "level": "FATAL", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "error", "level": "ERROR", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "warn", "level": "WARN", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "info", "level": "INFO", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "debug", "level": "DEBUG", "create_time": "2000-01-01T00:00:00Z"},
                            {"description": "trace", "level": "TRACE", "create_time": "2000-01-01T00:00:00Z"}
                        ]""",
                    ),
                },
                "levels": "TRACE",
                "expect": [
                    {
                        "description": "fatal",
                        "level": "FATAL",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                    {
                        "description": "error",
                        "level": "ERROR",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                    {
                        "description": "warn",
                        "level": "WARN",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                    {
                        "description": "info",
                        "level": "INFO",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                    {
                        "description": "debug",
                        "level": "DEBUG",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                    {
                        "description": "trace",
                        "level": "TRACE",
                        "create_time": "2000-01-01T00:00:00Z",
                    },
                ],
            },
        ]

        for test in tests:
            backend = bk.TerminalDisplayBackend(
                MockTerminalSystemAPIClient(test["responses"])
            )
            if test["levels"] is None:
                actual = backend.get_events()
            else:
                actual = backend.get_events(test["levels"])
            self.assertEqual(actual, test["expect"])

    def test_get_device_connectors(self):
        tests = [
            {
                "responses": {
                    "list_device_connectors": self.__new_response(
                        200,
                        """
                        [
                            {
                                "id": "can",
                                "service_id": "CAN-USB Interface",
                                "upstream_ipc_ids": [
                                    "up-can"
                                ],
                                "downstream_ipc_ids": [
                                    "down-can"
                                ],
                                "service_substitutions": [
                                    "DC_DEVICE_PATH=/dev/apt-usb/by-id/usb-aptpod__Inc._EP1-CH02A_0110000500015-if00"
                                ]
                            },
                            {
                                "id": "gps",
                                "service_id": "GPS",
                                "upstream_ipc_ids": [
                                    "up-gps"
                                ],
                                "downstream_ipc_ids": [],
                                "service_substitutions": []
                            }
                        ]
                        """,
                    ),
                    "list_device_connector_state_for_upstream": self.__new_response(
                        200,
                        """[
                            {"id":"up-can","code":"connected"},
                            {"id":"up-gps","code":"connected"}
                        ]""",
                    ),
                    "list_device_connector_state_for_downstream": self.__new_response(
                        200,
                        """[
                            {"id":"down-can","code":"disconnected","update_time":"2000-01-01T00:00:00Z"}
                        ]""",
                    ),
                    "list_device_connector_services": self.__new_response(
                        200,
                        """
                        [
                            {
                                "service_id": "CAN-USB Interface",
                                "substitution_variables": [
                                    {"key": "DC_DEVICE_PATH"}
                                ]
                            },
                            {
                                "service_id": "GPS",
                                "substitution_variables": []
                            }
                        ]
                        """,
                    ),
                },
                "expect": (
                    [
                        {
                            "id": "can",
                            "service_id": "CAN-USB Interface",
                            "upstream_ipc_ids": ["up-can"],
                            "downstream_ipc_ids": ["down-can"],
                            "service_substitutions": [
                                "DC_DEVICE_PATH=/dev/apt-usb/by-id/usb-aptpod__Inc._EP1-CH02A_0110000500015-if00"
                            ],
                            # appended items
                            "upstream_ipc_state": "connected",
                            "downstream_ipc_state": "disconnected",
                            "substitution_variables": [{"key": "DC_DEVICE_PATH"}],
                        },
                        {
                            "id": "gps",
                            "service_id": "GPS",
                            "upstream_ipc_ids": ["up-gps"],
                            "downstream_ipc_ids": [],
                            "service_substitutions": [],
                            # appended items
                            "upstream_ipc_state": "connected",
                            "substitution_variables": [],
                        },
                    ],
                    True,
                ),
            },
            {
                "responses": {
                    "list_device_connectors": self.__new_response(
                        200,
                        """
                        [
                            {
                                "id": "2up-2down",
                                "service_id": "2UP-2DOWN",
                                "upstream_ipc_ids": [
                                    "up1",
                                    "up2"
                                ],
                                "downstream_ipc_ids": [
                                    "down1",
                                    "down2"
                                ],
                                "service_substitutions": []
                            }
                        ]
                        """,
                    ),
                    "list_device_connector_state_for_upstream": self.__new_response(
                        200,
                        """[
                            {"id":"up1","code":"quiet"},
                            {"id":"up2","code":"connected"}
                        ]""",
                    ),
                    "list_device_connector_state_for_downstream": self.__new_response(
                        200,
                        """[
                            {"id":"down1","code":"connected","update_time":"2000-01-01T00:00:00Z"},
                            {"id":"down2","code":"disconnected","update_time":"2000-01-01T00:00:00Z"}
                        ]""",
                    ),
                    "list_device_connector_services": self.__new_response(
                        200,
                        """
                        [
                            {
                                "service_id": "2UP-2DOWN",
                                "substitution_variables": []
                            }
                        ]
                        """,
                    ),
                },
                "expect": (
                    [
                        {
                            "id": "2up-2down",
                            "service_id": "2UP-2DOWN",
                            "upstream_ipc_ids": ["up1", "up2"],
                            "downstream_ipc_ids": ["down1", "down2"],
                            "service_substitutions": [],
                            # appended items
                            "upstream_ipc_state": "quiet",
                            "downstream_ipc_state": "disconnected",
                            "substitution_variables": [],
                        }
                    ],
                    True,
                ),
            },
        ]

        for test in tests:
            backend = bk.TerminalDisplayBackend(
                MockTerminalSystemAPIClient(test["responses"])
            )
            actual = backend.get_device_connectors()
            self.assertEqual(actual, test["expect"])

    def test__list_device_connectors_state(self):
        test_filter = {
            "responses": {
                "list_device_connectors": self.__new_response(
                    200,
                    """
                    [
                        {
                            "id": "can",
                            "service_id": "CAN-USB Interface",
                            "enabled": true,
                            "upstream_ipc_ids": [
                                "up-can"
                            ],
                            "downstream_ipc_ids": [
                                "down-can"
                            ],
                            "service_substitutions": [
                                "DC_DEVICE_PATH=/dev/apt-usb/by-id/usb-aptpod__Inc._EP1-CH02A_0110000500015-if00"
                            ]
                        },
                        {
                            "id": "gps",
                            "service_id": "GPS",
                            "enabled": true,
                            "upstream_ipc_ids": [
                                "up-gps"
                            ],
                            "downstream_ipc_ids": [],
                            "service_substitutions": []
                        }
                    ]
                    """,
                ),
                "list_device_connector_state_for_upstream": self.__new_response(
                    200,
                    """[{"id":"up-can","code":"connected"},{"id":"up-gps","code":"connected"}]""",
                ),
                "list_device_connector_state_for_downstream": self.__new_response(
                    200,
                    """[{"id":"down-can","code":"disconnected","update_time":"2000-01-01T00:00:00Z"}]""",
                ),
            },
            "expect_no_filter": (
                (
                    [
                        {"id": "up-can", "code": "connected"},
                        {"id": "up-gps", "code": "connected"},
                    ],
                    [
                        {
                            "id": "down-can",
                            "code": "disconnected",
                            "update_time": "2000-01-01T00:00:00Z",
                        }
                    ],
                    [
                        "/agent/device_connectors_upstream/up-can",
                        "/agent/device_connectors_upstream/up-gps",
                    ],
                    ["/agent/device_connectors_downstream/down-can"],
                ),
                True,
            ),
            "expect_filter_can": (
                (
                    [{"id": "up-can", "code": "connected"}],
                    [
                        {
                            "id": "down-can",
                            "code": "disconnected",
                            "update_time": "2000-01-01T00:00:00Z",
                        }
                    ],
                    ["/agent/device_connectors_upstream/up-can"],
                    ["/agent/device_connectors_downstream/down-can"],
                ),
                True,
            ),
            "expect_filter_gps": (
                (
                    [{"id": "up-gps", "code": "connected"}],
                    [],
                    ["/agent/device_connectors_upstream/up-gps"],
                    [],
                ),
                True,
            ),
            "expect_filter_unmatched": (
                (
                    [],
                    [],
                    [],
                    [],
                ),
                True,
            ),
        }
        tests_error_response = [
            {
                "responses": {
                    "list_device_connectors": self.__new_response(500, "{}"),
                    "list_device_connector_state_for_upstream": self.__new_response(
                        200, "{}"
                    ),
                    "list_device_connector_state_for_downstream": self.__new_response(
                        200, "{}"
                    ),
                },
                "expect": (
                    (),
                    False,
                ),
            },
            {
                "responses": {
                    "list_device_connectors": self.__new_response(
                        200,
                        """
                        [
                            {
                                "id": "can",
                                "service_id": "CAN-USB Interface",
                                "enabled": true,
                                "upstream_ipc_ids": [
                                    "up-can"
                                ],
                                "downstream_ipc_ids": [
                                    "down-can"
                                ],
                                "service_substitutions": [
                                    "DC_DEVICE_PATH=/dev/apt-usb/by-id/usb-aptpod__Inc._EP1-CH02A_0110000500015-if00"
                                ]
                            },
                            {
                                "id": "gps",
                                "service_id": "GPS",
                                "enabled": true,
                                "upstream_ipc_ids": [
                                    "up-gps"
                                ],
                                "downstream_ipc_ids": [],
                                "service_substitutions": []
                            }
                        ]
                        """,
                    ),
                    "list_device_connector_state_for_upstream": self.__new_response(
                        500, "{}"
                    ),
                    "list_device_connector_state_for_downstream": self.__new_response(
                        200, "{}"
                    ),
                },
                "expect": (
                    (),
                    False,
                ),
            },
            {
                "responses": {
                    "list_device_connectors": self.__new_response(
                        200,
                        """
                        [
                            {
                                "id": "can",
                                "service_id": "CAN-USB Interface",
                                "enabled": true,
                                "upstream_ipc_ids": [
                                    "up-can"
                                ],
                                "downstream_ipc_ids": [
                                    "down-can"
                                ],
                                "service_substitutions": [
                                    "DC_DEVICE_PATH=/dev/apt-usb/by-id/usb-aptpod__Inc._EP1-CH02A_0110000500015-if00"
                                ]
                            },
                            {
                                "id": "gps",
                                "service_id": "GPS",
                                "enabled": true,
                                "upstream_ipc_ids": [
                                    "up-gps"
                                ],
                                "downstream_ipc_ids": [],
                                "service_substitutions": []
                            }
                        ]
                        """,
                    ),
                    "list_device_connector_state_for_upstream": self.__new_response(
                        200, "{}"
                    ),
                    "list_device_connector_state_for_downstream": self.__new_response(
                        500, "{}"
                    ),
                },
                "expect": (
                    (),
                    False,
                ),
            },
        ]

        backend = bk.TerminalDisplayBackend(
            MockTerminalSystemAPIClient(test_filter["responses"])
        )
        actual = backend._list_device_connectors_state("")
        self.assertEqual(actual, test_filter["expect_no_filter"])
        actual = backend._list_device_connectors_state("CAN-USB Interface")
        self.assertEqual(actual, test_filter["expect_filter_can"])
        actual = backend._list_device_connectors_state("GPS")
        self.assertEqual(actual, test_filter["expect_filter_gps"])
        actual = backend._list_device_connectors_state("UNMATCHED_PATTERN")
        self.assertEqual(actual, test_filter["expect_filter_unmatched"])

        for test in tests_error_response:
            backend = bk.TerminalDisplayBackend(
                MockTerminalSystemAPIClient(test["responses"])
            )
            actual = backend._list_device_connectors_state("")
            self.assertEqual(actual, test["expect"])

    def test__aggregate_state(self):
        tests = [
            # expect none
            {
                "status": [
                    {},
                    {"code": "none", "update_time": "2000-01-01T00:00:01Z"},
                ],
                "expect": ("none", datetime(2000, 1, 1, 0, 0, 1)),
            },
            # expect disconnected
            {
                "status": [
                    {"code": "disconnected", "update_time": "2000-01-01T00:00:00Z"},
                    {},
                ],
                "expect": ("disconnected", datetime(2000, 1, 1, 0, 0, 0)),
            },
            {
                "status": [
                    {"code": "disconnected", "update_time": "2000-01-01T00:00:00Z"},
                    {"code": "quiet", "update_time": "2000-01-01T00:00:01Z"},
                ],
                "expect": ("disconnected", datetime(2000, 1, 1, 0, 0, 1)),
            },
            {
                "status": [
                    {"code": "disconnected", "update_time": "2000-01-01T00:00:00Z"},
                    {"code": "connected", "update_time": "2000-01-01T00:00:01Z"},
                ],
                "expect": ("disconnected", datetime(2000, 1, 1, 0, 0, 1)),
            },
            {
                "status": [
                    {"code": "disconnected", "update_time": "2000-01-01T00:00:00Z"},
                    {"code": "quiet", "update_time": "2000-01-01T00:00:01Z"},
                    {"code": "connected", "update_time": "2000-01-01T00:00:02Z"},
                ],
                "expect": ("disconnected", datetime(2000, 1, 1, 0, 0, 2)),
            },
            # expect connected
            {
                "status": [
                    {"code": "connected", "update_time": None},
                ],
                "expect": ("connected", None),
            },
            # expect quiet
            {
                "status": [
                    {"code": "connected", "update_time": None},
                    {"code": "quiet", "update_time": None},
                ],
                "expect": ("quiet", None),
            },
            {
                "status": [
                    {"code": "quiet", "update_time": "2000-01-01T00:00:00Z"},
                ],
                "expect": ("quiet", datetime(2000, 1, 1, 0, 0, 0)),
            },
        ]

        for test in tests:
            backend = bk.TerminalDisplayBackend(MockTerminalSystemAPIClient(None))
            actual = backend._aggregate_state(test["status"])
            self.assertEqual(actual, test["expect"])

    def test__aggregate_pending_data_size(self):
        tests = [
            {
                "measurements": [
                    {"pending_data_size": 1},
                    {"pending_data_size": 2},
                    {"pending_data_size": 3},
                ],
                "expect": 6,
            },
        ]

        for test in tests:
            backend = bk.TerminalDisplayBackend(MockTerminalSystemAPIClient(None))
            actual = backend._aggregate_pending_data_size(test["measurements"])
            self.assertEqual(actual, test["expect"])

    def test__filter_device_connectors_by_service_id(self):
        device_connectors = [
            {"service_id": "ANALOG-USB Interface"},
            {"service_id": "Audio (Onboard)"},
            {"service_id": "CAN-USB Interface"},
            {"service_id": "CAN-USB Interface (Upstream)"},
            {"service_id": "CAN-USB Interface (Downstream)"},
            {"service_id": "GPS"},
            {"service_id": "H.264 NAL Unit for EDGEPLANT USB Camera"},
            {"service_id": "H.264 for EDGEPLANT USB Camera"},
            {"service_id": "H.264 for EDGEPLANT USB Camera x4"},
            {"service_id": "H.264 for EDGEPLANT USB Camera (v4l2-src)"},
            {"service_id": "MJPEG for EDGEPLANT USB Camera"},
            {"service_id": "MJPEG for EDGEPLANT USB Camera (v4l2-src)"},
        ]
        tests = [
            {
                "pattern": "GPS",
                "device_connectors": device_connectors,
                "expect": ([{"service_id": "GPS"}]),
            },
            {
                "pattern": "CAN-USB Interface",
                "device_connectors": device_connectors,
                "expect": (
                    [
                        {"service_id": "CAN-USB Interface"},
                        {"service_id": "CAN-USB Interface (Upstream)"},
                        {"service_id": "CAN-USB Interface (Downstream)"},
                    ]
                ),
            },
            {
                "pattern": "Camera",
                "device_connectors": device_connectors,
                "expect": (
                    [
                        {"service_id": "H.264 NAL Unit for EDGEPLANT USB Camera"},
                        {"service_id": "H.264 for EDGEPLANT USB Camera"},
                        {"service_id": "H.264 for EDGEPLANT USB Camera x4"},
                        {"service_id": "H.264 for EDGEPLANT USB Camera (v4l2-src)"},
                        {"service_id": "MJPEG for EDGEPLANT USB Camera"},
                        {"service_id": "MJPEG for EDGEPLANT USB Camera (v4l2-src)"},
                    ]
                ),
            },
        ]

        for test in tests:
            backend = bk.TerminalDisplayBackend(MockTerminalSystemAPIClient(None))
            actual = backend._filter_device_connectors_by_service_id(
                test["pattern"], test["device_connectors"]
            )
            self.assertEqual(actual, test["expect"])

    def test__filter_state_by_id(self):
        tests = [
            {
                "ipc_ids": ["b"],
                "status": [
                    {"id": "a", "key": "val"},
                    {"id": "b", "key": "val"},
                    {"id": "c", "key": "val"},
                ],
                "expect": ([{"id": "b", "key": "val"}]),
            },
        ]

        for test in tests:
            backend = bk.TerminalDisplayBackend(MockTerminalSystemAPIClient(None))
            actual = backend._filter_state_by_ids(test["ipc_ids"], test["status"])
            self.assertEqual(actual, test["expect"])

    def test__utc_rfc3339_to_datetime(self):
        tests = [
            {
                "ts": None,
                "expect": None,
            },
            {
                "ts": "2006-01-02T15:04:05Z",
                "expect": datetime(2006, 1, 2, 15, 4, 5),
            },
        ]

        for test in tests:
            backend = bk.TerminalDisplayBackend(MockTerminalSystemAPIClient(None))
            actual = backend._utc_rfc3339_to_datetime(test["ts"])
            self.assertEqual(actual, test["expect"])

    def __new_response(self, status_code, content):
        resp = requests.Response()
        resp.status_code = status_code
        resp._content = bytes(content, "utf-8")
        return resp


if __name__ == "__main__":
    unittest.main()
