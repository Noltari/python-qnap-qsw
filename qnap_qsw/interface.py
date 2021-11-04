# -*- coding: utf-8 -*-
"""Client for the QNAP QSW API."""

import base64
import logging
from http import HTTPStatus

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
        if not _host.endswith(API_URI):
            _host = f"{_host}/{API_URI}"
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

        try:
            result = response.json()
        except ValueError:
            result = None

        return result

    def config_url(self):
        """Config URL."""
        return self.api_url[: self.api_url.rfind(API_URI)]

    def debugging(self, debug):
        """Enable/Disable debugging."""
        self.debug = debug
        return self.debug

    def get_about(self):
        """Get API about."""
        return self.api_call("about")

    def get_acl_mac(self):
        """Get ACL mac."""
        return self.api_call("v1/acl/mac")

    def get_acl_ip(self):
        """Get ACL IP."""
        return self.api_call("v1/acl/ip")

    def get_acl_ports(self):
        """Get ACL ports."""
        return self.api_call("v1/acl/ports")

    def get_dns_server(self):
        """Get DNS server."""
        return self.api_call("v1/dns/server")

    def get_firmware_condition(self):
        """Get firmware condition."""
        return self.api_call("v1/firmware/condition")

    def get_firmware_info(self):
        """Get firmware info."""
        return self.api_call("v1/firmware/info")

    def get_firmware_update(self):
        """Get firmware update."""
        return self.api_call("v1/firmware/update")

    def get_firmware_update_check(self):
        """Get firmware update check."""
        return self.api_call("v1/firmware/update/check")

    def get_firmware_status(self):
        """Get firmware update status."""
        return self.api_call("v1/firmware/status")

    def get_igmp(self):
        """Get IGMP."""
        return self.api_call("v1/igmp")

    def get_igmp_group_status(self):
        """Get IGMP group status."""
        return self.api_call("v1/igmp/group/status")

    def get_igmp_port_interface(self):
        """Get IGMP port interface."""
        return self.api_call("v1/igmp/port/interface")

    def get_igmp_vlan_interface(self):
        """Get IGMP VLAN interface."""
        return self.api_call("v1/igmp/vlan/interface")

    def get_ipv4_interface(self):
        """Get IPv4 interface."""
        return self.api_call("v1/ip/ipv4/interface")

    def get_ipv4_interface_status(self):
        """Get IPv4 interface status."""
        return self.api_call("v1/ip/ipv4/interface/status")

    def get_ipv4_route_status(self):
        """Get IPv4 route status."""
        return self.api_call("v1/ip/ipv4/route/status")

    def get_lacp_group(self):
        """Get LACP group."""
        return self.api_call("v1/lacp/group")

    def get_lacp_info(self):
        """Get LACP info."""
        return self.api_call("v1/lacp/info")

    def get_live(self):
        """Get API live."""
        return self.api_call("live")

    def get_lldp(self):
        """Get LLDP."""
        return self.api_call("v1/lldp")

    def get_lldp_interface(self):
        """Get LLDP interface."""
        return self.api_call("v1/lldp/interface")

    def get_lldp_neighbors_status(self):
        """Get LLDP neighbors status."""
        return self.api_call("v1/lldp/neighbors/status")

    def get_mac(self):
        """Get mac FDB status."""
        return self.api_call("v1/mac")

    def get_mac_fdb_status(self):
        """Get mac FDB status."""
        return self.api_call("v1/mac/fdb/status")

    def get_mirror(self):
        """Get mirror."""
        return self.api_call("v1/mirror")

    def get_ports(self):
        """Get ports."""
        return self.api_call("v1/ports")

    def get_ports_ethernet(self):
        """Get ports ethernet."""
        return self.api_call("v1/ports/ethernet")

    def get_ports_fec(self):
        """Get ports FEC."""
        return self.api_call("v1/ports/fec")

    def get_ports_resource(self):
        """Get ports resource."""
        return self.api_call("v1/ports/resource")

    def get_ports_status(self):
        """Get ports status."""
        return self.api_call("v1/ports/status")

    def get_ports_statistics(self):
        """Get ports statistics."""
        return self.api_call("v1/ports/statistics")

    def get_ports_transceiver(self):
        """Get ports transceiver."""
        return self.api_call("v1/ports/transceiver")

    def get_qos_default(self):
        """Get QoS default."""
        return self.api_call("v1/qos/default")

    def get_qos_mode(self):
        """Get QoS mode."""
        return self.api_call("v1/qos/mode")

    def get_qos_pcp(self):
        """Get QoS PCP."""
        return self.api_call("v1/qos/pcp")

    def get_rstp(self):
        """Get RSTP."""
        return self.api_call("v1/rstp")

    def get_rstp_interface(self):
        """Get RSTP interface."""
        return self.api_call("v1/rstp/interface")

    def get_rstp_interface_role(self):
        """Get RSTP interface role."""
        response = self.api_call("v1/rstp/interface/role")
        return response

    def get_rstp_interface_state(self):
        """Get RSTP interface state."""
        return self.api_call("v1/rstp/interface/state")

    def get_rstp_priority(self):
        """Get RSTP interface."""
        return self.api_call("v1/rstp/priority")

    def get_sntp(self):
        """Get SNTP."""
        return self.api_call("v1/sntp")

    def get_sntp_server(self):
        """Get SNTP server."""
        return self.api_call("v1/sntp/server")

    def get_sntp_status(self):
        """Get SNTP status."""
        return self.api_call("v1/sntp/status")

    def get_sntp_timezone(self):
        """Get SNTP timezone."""
        return self.api_call("v1/sntp/timezone")

    def get_system_board(self):
        """Get system board."""
        return self.api_call("v1/system/board")

    def get_system_config(self):
        """Get system config."""
        return self.api_call("v1/system/config")

    def get_system_clock(self):
        """Get system clock."""
        return self.api_call("v1/system/clock")

    def get_system_https(self):
        """Get system https."""
        return self.api_call("v1/system/https")

    def get_system_info(self):
        """Get system info."""
        return self.api_call("v1/system/info")

    def get_system_sensor(self):
        """Get system sensor."""
        return self.api_call("v1/system/sensor")

    def get_system_time(self):
        """Get system time."""
        return self.api_call("v1/system/time")

    def get_system_web_config(self):
        """Get system web config."""
        return self.api_call("v1/system/web/config")

    def get_users_verification(self):
        """Get users verification."""
        return self.api_call("v1/users/verification")

    def get_vlan(self):
        """Get VLAN."""
        return self.api_call("v1/vlan")

    def get_vlan_indexs(self):
        """Get VLAN indexs."""
        return self.api_call("v1/vlan/indexs")

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
        response = self.post_users_login(json)

        if not response:
            return None
        if (
            ATTR_ERROR_CODE not in response
            or response[ATTR_ERROR_CODE] != HTTPStatus.OK
        ):
            return None

        self.api_key = response[ATTR_RESULT]
        self.cookies[API_QSW_ID] = self.api_key
        self.headers[API_AUTHORIZATION] = "Bearer " + self.api_key

        return response

    def logout(self):
        """User logout."""
        json = {}
        response = self.post_users_exit(json)

        self.api_key = None
        if self.cookies and API_QSW_ID in self.cookies:
            del self.cookies[API_QSW_ID]
        if self.headers and API_AUTHORIZATION in self.headers:
            del self.headers[API_AUTHORIZATION]

        return response

    def post_system_command(self, command):
        """Post system command."""
        json = {ATTR_COMMAND: command}
        return self.api_call("v1/system/command", method="POST", json=json)

    def post_users_exit(self, json):
        """Post users exit."""
        return self.api_call("v1/users/exit", method="POST", json=json)

    def post_users_login(self, json):
        """Post users login."""
        return self.api_call("v1/users/login", method="POST", json=json)

    def put_user_password(self, user, password):
        """Put user password."""
        json = {ATTR_IDX: user, ATTR_DATA: {ATTR_PASSWORD: password}}
        return self.api_call("v1/users", method="PUT", json=json)
