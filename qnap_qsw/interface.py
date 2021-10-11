# -*- coding: utf-8 -*-
"""Client for the QNAP QSW API."""

import base64
import logging

import requests
import urllib3
from requests.exceptions import RequestException
from urllib3.exceptions import ConnectTimeoutError, InsecureRequestWarning

from .const import (
    API_AUTHORIZATION,
    API_DEBUG,
    API_QSW_ID,
    API_QSW_LANG,
    API_TIMEOUT,
    API_URI,
    API_URI_FULL,
    API_URI_V1,
    API_VERIFY,
    ATTR_COMMAND,
    ATTR_DATA,
    ATTR_ERROR_CODE,
    ATTR_IDX,
    ATTR_PASSWORD,
    ATTR_RESULT,
    ATTR_USERNAME,
)

_LOGGER = logging.getLogger(__name__)


class QSAException(Exception):
    """Raised when QNAP API call resulted in exception."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


# pylint: disable=R0904
class QSA:
    """Interacts with the QNAP QSW API."""

    # pylint: disable=R0902
    def __init__(self, host):
        """Init QNAP QSW API."""
        _host = host.strip()
        if not _host.startswith("http://") and not _host.startswith("https://"):
            _host = f"http://{_host}"
        if _host.endswith("/"):
            _host = _host[:-1]
        if _host.endswith(API_URI):
            _host = f"{_host}/{API_URI_V1}"
        if not _host.endswith(API_URI_FULL):
            _host = f"{_host}/{API_URI_FULL}"
        self.api_url = _host
        self.api_key = None
        self.cookies = {API_QSW_LANG: "ENG"}
        self.debug = API_DEBUG
        self.headers = {}
        self.session = requests.Session()
        self.timeout = API_TIMEOUT
        # Invalid QNAP HTTPS certificate
        self.verify = API_VERIFY
        urllib3.disable_warnings(category=InsecureRequestWarning)

    def api_call(self, cmd, method="GET", json=None):
        """Perform Rest API call."""
        url = f"{self.api_url}/{cmd}"

        if self.debug:
            _LOGGER.warning("api call: %s/%s", self.api_url, cmd)

        try:
            response = self.session.request(
                method,
                url,
                json=json,
                cookies=self.cookies,
                headers=self.headers,
                timeout=self.timeout,
                verify=self.verify,
            )
        except RequestException as err:
            raise QSAException(err) from err
        except ConnectTimeoutError as err:
            raise QSAException(err) from err

        if self.debug:
            _LOGGER.warning(
                "api_call: %s, status: %s, response %s",
                cmd,
                response.status_code,
                response.text,
            )

        str_response = response.text
        if str_response is None or str_response == "":
            return None

        try:
            return response.json()
        except ValueError:
            return str_response

    def config_url(self):
        """Config URL."""
        return self.api_url[: self.api_url.rfind(API_URI_FULL)]

    def debugging(self, debug):
        """Enable/Disable debugging."""
        self.debug = debug
        return self.debug

    def get_acl_ip(self):
        """Get ACL IP."""
        return self.api_call("acl/ip")

    def get_acl_ports(self):
        """Get ACL ports."""
        return self.api_call("acl/ports")

    def get_dns_server(self):
        """Get IPv4 route status."""
        return self.api_call("dns/server")

    def get_firmware_condition(self):
        """Get firmware condition."""
        return self.api_call("firmware/condition")

    def get_firmware_info(self):
        """Get firmware info."""
        return self.api_call("firmware/info")

    def get_firmware_update_check(self):
        """Get firmware update check."""
        return self.api_call("firmware/update/check")

    def get_igmp(self):
        """Get IGMP."""
        return self.api_call("igmp")

    def get_igmp_port_interface(self):
        """Get IGMP port interface."""
        return self.api_call("igmp/port/interface")

    def get_igmp_vlan_interface(self):
        """Get IGMP VLAN interface."""
        return self.api_call("igmp/vlan/interface")

    def get_ipv4_interface(self):
        """Get IPv4 interface."""
        return self.api_call("ip/ipv4/interface")

    def get_ipv4_interface_status(self):
        """Get IPv4 interface status."""
        return self.api_call("ip/ipv4/interface/status")

    def get_ipv4_route_status(self):
        """Get IPv4 route status."""
        return self.api_call("ip/ipv4/route/status")

    def get_lacp_group(self):
        """Get LACP group."""
        return self.api_call("lacp/group")

    def get_lacp_info(self):
        """Get LACP info."""
        return self.api_call("lacp/info")

    def get_lldp(self):
        """Get LLDP."""
        return self.api_call("lldp")

    def get_lldp_port_interface(self):
        """Get LLDP interface."""
        return self.api_call("lldp/interface")

    def get_ports(self):
        """Get ports."""
        return self.api_call("ports")

    def get_ports_resource(self):
        """Get ports resource."""
        return self.api_call("ports/resource")

    def get_ports_status(self):
        """Get ports status."""
        return self.api_call("ports/status")

    def get_qos_default(self):
        """Get QoS default."""
        return self.api_call("qos/default")

    def get_qos_mode(self):
        """Get QoS mode."""
        return self.api_call("qos/mode")

    def get_rstp(self):
        """Get RSTP."""
        return self.api_call("rstp")

    def get_rstp_interface(self):
        """Get RSTP interface."""
        return self.api_call("rstp/interface")

    def get_rstp_interface_role(self):
        """Get RSTP interface role."""
        response = self.api_call("rstp/interface/role")
        return response

    def get_rstp_interface_state(self):
        """Get RSTP interface state."""
        return self.api_call("rstp/interface/state")

    def get_rstp_priority(self):
        """Get RSTP interface."""
        return self.api_call("rstp/priority")

    def get_sntp(self):
        """Get SNTP."""
        return self.api_call("sntp")

    def get_sntp_timezone(self):
        """Get SNTP timezone."""
        return self.api_call("sntp/timezone")

    def get_system_board(self):
        """Get system board."""
        return self.api_call("system/board")

    def get_system_config(self):
        """Get system config."""
        return self.api_call("system/config")

    def get_system_clock(self):
        """Get system clock."""
        return self.api_call("system/clock")

    def get_system_https(self):
        """Get system https."""
        return self.api_call("system/https")

    def get_system_info(self):
        """Get system info."""
        return self.api_call("system/info")

    def get_system_sensor(self):
        """Get system sensor."""
        return self.api_call("system/sensor")

    def get_system_time(self):
        """Get system time."""
        return self.api_call("system/time")

    def get_system_web_config(self):
        """Get system web config."""
        return self.api_call("system/web/config")

    def get_vlan(self):
        """Get VLAN."""
        return self.api_call("vlan")

    def login(self, user, password):
        """User login."""
        self.api_key = None
        if self.cookies and API_QSW_ID in self.cookies:
            del self.cookies[API_QSW_ID]
        if self.headers and API_AUTHORIZATION in self.headers:
            del self.headers[API_AUTHORIZATION]

        b64_pass = base64.b64encode(password.encode("utf-8")).decode("utf-8")
        json = {
            ATTR_USERNAME: user,
            ATTR_PASSWORD: b64_pass,
        }
        response = self.api_call("users/login", method="POST", json=json)

        if not response:
            return None
        if ATTR_ERROR_CODE not in response or response[ATTR_ERROR_CODE] != 200:
            return None

        self.api_key = response[ATTR_RESULT]
        self.cookies[API_QSW_ID] = self.api_key
        self.headers[API_AUTHORIZATION] = "Bearer " + self.api_key

        return response

    def logout(self):
        """User logout."""
        response = self.api_call("users/exit", method="POST", json={})

        self.api_key = None
        if self.cookies and API_QSW_ID in self.cookies:
            del self.cookies[API_QSW_ID]
        if self.headers and API_AUTHORIZATION in self.headers:
            del self.headers[API_AUTHORIZATION]

        return response

    def post_system_command(self, command):
        """Post system command."""
        json = {ATTR_COMMAND: command}
        return self.api_call("system/command", method="POST", json=json)

    def put_user_password(self, user, password):
        """Put user password."""
        json = {ATTR_IDX: user, ATTR_DATA: {ATTR_PASSWORD: password}}
        return self.api_call("users", method="PUT", json=json)
