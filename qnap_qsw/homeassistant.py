# -*- coding: utf-8 -*-
"""Home Assistant client for the QNAP QSW API."""

import logging
import re
from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from .const import (
    ATTR_ANOMALY,
    ATTR_ERROR_CODE,
    ATTR_ERROR_MESSAGE,
    ATTR_FAN1SPEED,
    ATTR_FAN2SPEED,
    ATTR_MAC,
    ATTR_MESSAGE,
    ATTR_MODEL,
    ATTR_NEWER,
    ATTR_NUM_PORTS,
    ATTR_NUMBER,
    ATTR_PRODUCT,
    ATTR_REBOOT,
    ATTR_RESULT,
    ATTR_SERIAL,
    ATTR_TEMP,
    ATTR_TEMP_MAX,
    ATTR_UPTIME,
    ATTR_VERSION,
    DATA_CONDITION_ANOMALY,
    DATA_CONDITION_MESSAGE,
    DATA_CONFIG_URL,
    DATA_FAN1_SPEED,
    DATA_FAN2_SPEED,
    DATA_FAN_COUNT,
    DATA_FIRMWARE,
    DATA_MAC_ADDR,
    DATA_MODEL,
    DATA_PRODUCT,
    DATA_SERIAL,
    DATA_TEMP,
    DATA_TEMP_MAX,
    DATA_UPDATE,
    DATA_UPDATE_VERSION,
    DATA_UPTIME,
    DATA_UPTIME_SECONDS,
    UPTIME_DELTA,
)
from .interface import QSA, QSAException

_LOGGER = logging.getLogger(__name__)


class LoginError(Exception):
    """Raised when QNAP API request ended in unautorized."""

    def __init__(self, status: str) -> None:
        """Initialize."""
        super().__init__(status)
        self.status = status


class QSHAData:
    """Stores data from QNAP QSW API for Home Assistant."""

    # pylint: disable=R0902
    def __init__(self):
        """Init QNAP QSW data for Home Assistant."""
        self.condition_anomaly = False
        self.condition_message = None
        self.firmware = None
        self.fan_speed = [None] * 2
        self.mac = None
        self.model = None
        self.num_ports = None
        self.product = None
        self.serial = None
        self.temp = None
        self.temp_max = None
        self.update = False
        self.update_version = None
        self.uptime = None
        self.uptime_seconds = None

    def set_firmware_condition(self, firmware_condition):
        """Set firmware/condition data."""
        if firmware_condition:
            self.condition_anomaly = firmware_condition[ATTR_RESULT][ATTR_ANOMALY]
            _msg = firmware_condition[ATTR_RESULT][ATTR_MESSAGE]
            if self.condition_anomaly and _msg and len(_msg) > 0:
                self.condition_message = _msg
            else:
                self.condition_message = None

    def set_firmware_info(self, firmware_info):
        """Set firmware/info data."""
        if firmware_info:
            self.firmware = (
                f"{firmware_info[ATTR_RESULT][ATTR_VERSION]}."
                f"{firmware_info[ATTR_RESULT][ATTR_NUMBER]}"
            )

    def set_firmware_update(self, firmware_update):
        """Set firmware/update data."""
        if firmware_update:
            self.update = firmware_update[ATTR_RESULT][ATTR_NEWER]
            if self.update:
                self.update_version = (
                    f"{firmware_update[ATTR_RESULT][ATTR_VERSION]}."
                    f"{firmware_update[ATTR_RESULT][ATTR_NUMBER]}"
                )
            else:
                self.update_version = None

    def set_system_board(self, system_board):
        """Set system/board data."""
        if system_board:
            self.mac = system_board[ATTR_RESULT][ATTR_MAC]
            self.model = system_board[ATTR_RESULT][ATTR_MODEL]
            self.num_ports = system_board[ATTR_RESULT][ATTR_NUM_PORTS]
            self.product = system_board[ATTR_RESULT][ATTR_PRODUCT]
            self.serial = system_board[ATTR_RESULT][ATTR_SERIAL]

    def set_system_sensor(self, system_sensor):
        """Set system/sensor data."""
        if system_sensor:
            if system_sensor[ATTR_RESULT][ATTR_FAN1SPEED] >= 0:
                self.fan_speed[0] = system_sensor[ATTR_RESULT][ATTR_FAN1SPEED]
            else:
                self.fan_speed[0] = None
            if system_sensor[ATTR_RESULT][ATTR_FAN2SPEED] >= 0:
                self.fan_speed[1] = system_sensor[ATTR_RESULT][ATTR_FAN2SPEED]
            else:
                self.fan_speed[1] = None
            self.temp = system_sensor[ATTR_RESULT][ATTR_TEMP]
            self.temp_max = system_sensor[ATTR_RESULT][ATTR_TEMP_MAX]

    def set_system_time(self, system_time, utcnow):
        """Set system/time data."""
        if system_time:
            self.uptime_seconds = system_time[ATTR_RESULT][ATTR_UPTIME]
            if self.uptime:
                new_uptime = (utcnow - timedelta(seconds=self.uptime_seconds)).replace(
                    microsecond=0, tzinfo=timezone.utc
                )
                if abs((new_uptime - self.uptime).total_seconds()) > UPTIME_DELTA:
                    self.uptime = new_uptime
            else:
                self.uptime = (utcnow - timedelta(seconds=self.uptime_seconds)).replace(
                    microsecond=0, tzinfo=timezone.utc
                )


# pylint: disable=R0904
class QSHA:
    """Gathers data from QNAP QSW API for Home Assistant."""

    def __init__(self, host, user, password):
        """Init QNAP QSW API for Home Assistant."""
        self.user = user
        self.password = password
        self.qsa = QSA(host)
        self.qsha_data = QSHAData()
        self._login = False

    def api_response(self, cmd, result):
        """Process response from QNAP QSW API."""
        if result[ATTR_ERROR_CODE] == HTTPStatus.UNAUTHORIZED:
            self.logout()
            raise LoginError("API returned unauthorized status")
        if result[ATTR_ERROR_CODE] != HTTPStatus.OK:
            _LOGGER.warning(
                '%s: Status[%s]="%s"',
                {cmd},
                {result[ATTR_ERROR_CODE]},
                {result[ATTR_ERROR_MESSAGE]},
            )
            return False
        return True

    def condition_anomaly(self) -> bool:
        """Get condition anomaly."""
        return self.qsha_data.condition_anomaly

    def condition_message(self) -> str:
        """Get condition message."""
        return self.qsha_data.condition_message

    def config_url(self) -> str:
        """Get configuration URL."""
        return self.qsa.config_url()

    def data(self):
        """Get data Dict."""
        _data = {
            DATA_CONDITION_ANOMALY: self.condition_anomaly(),
            DATA_CONDITION_MESSAGE: self.condition_message(),
            DATA_CONFIG_URL: self.config_url(),
            DATA_FAN_COUNT: self.fan_count(),
            DATA_FIRMWARE: self.firmware(),
            DATA_MAC_ADDR: self.mac_addr(),
            DATA_MODEL: self.model(),
            DATA_PRODUCT: self.product(),
            DATA_SERIAL: self.serial(),
            DATA_TEMP: self.temp(),
            DATA_TEMP_MAX: self.temp_max(),
            DATA_UPDATE: self.update(),
            DATA_UPDATE_VERSION: self.update_version(),
            DATA_UPTIME: self.uptime(),
            DATA_UPTIME_SECONDS: self.uptime_seconds(),
        }

        if self.fan_count() > 0:
            _data[DATA_FAN1_SPEED] = self.fan_speed(0)
        if self.fan_count() > 1:
            _data[DATA_FAN2_SPEED] = self.fan_speed(1)

        return _data

    def fan_count(self) -> int:
        """Get number of fans."""
        fans = self.qsha_data.fan_speed
        count = 0
        for fan in fans:
            if fan:
                count = count + 1
        return count

    def fan_speed(self, idx) -> int:
        """Get fan speed."""
        if idx > len(self.qsha_data.fan_speed):
            return None
        return self.qsha_data.fan_speed[idx]

    def firmware(self) -> str:
        """Get firmware version."""
        return self.qsha_data.firmware

    def login(self) -> bool:
        """Login."""
        if not self._login:
            if self.qsa.login(self.user, self.password):
                self._login = True
        return self._login

    def logout(self):
        """Logout."""
        if self._login:
            self.qsa.logout()
        self._login = False

    def mac_addr(self) -> str:
        """Get MAC address."""
        return self.qsha_data.mac

    def model(self) -> str:
        """Get product model."""
        return self.qsha_data.model

    def product(self) -> str:
        """Get product name."""
        return self.qsha_data.product

    def reboot(self):
        """Reboot QNAP QSW switch."""
        if self.login():
            response = self.qsa.post_system_command(ATTR_REBOOT)
            if (
                response
                and response[ATTR_ERROR_CODE] == HTTPStatus.OK
                and not response[ATTR_RESULT]
            ):
                return True

        return False

    def serial(self) -> str:
        """Get serial number."""
        _serial = self.qsha_data.serial
        if _serial:
            return re.sub(r"[\W_]+", "", _serial)
        return None

    def temp(self) -> int:
        """Get current temperature."""
        return self.qsha_data.temp

    def temp_max(self) -> int:
        """Get max temperature."""
        return self.qsha_data.temp_max

    def update(self) -> bool:
        """Get firmware update."""
        return self.qsha_data.update

    def update_version(self) -> str:
        """Get firmware update version."""
        return self.qsha_data.update_version

    def update_firmware_condition(self):
        """Update firmware/condition from QNAP QSW API."""
        try:
            firmware_condition = self.qsa.get_firmware_condition()
            if firmware_condition and self.api_response(
                "firmware/condition", firmware_condition
            ):
                self.qsha_data.set_firmware_condition(firmware_condition)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_firmware_info(self):
        """Update firmware/info from QNAP QSW API."""
        try:
            firmware_info = self.qsa.get_firmware_info()
            if firmware_info and self.api_response("firmware/info", firmware_info):
                self.qsha_data.set_firmware_info(firmware_info)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_firmware_update_check(self):
        """Update firmware/update/check from QNAP QSW API."""
        try:
            firmware_update = self.qsa.get_firmware_update_check()
            if firmware_update and self.api_response(
                "firmware/update/check", firmware_update
            ):
                self.qsha_data.set_firmware_update(firmware_update)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_system_board(self):
        """Update system/board from QNAP QSW API."""
        try:
            system_board = self.qsa.get_system_board()
            if system_board and self.api_response("system/board", system_board):
                self.qsha_data.set_system_board(system_board)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_system_sensor(self):
        """Update system/sensor from QNAP QSW API."""
        try:
            system_sensor = self.qsa.get_system_sensor()
            if system_sensor and self.api_response("system/sensor", system_sensor):
                self.qsha_data.set_system_sensor(system_sensor)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_system_time(self):
        """Update system/time from QNAP QSW API."""
        try:
            system_time = self.qsa.get_system_time()
            utcnow = datetime.utcnow()
            if system_time and self.api_response("system/time", system_time):
                self.qsha_data.set_system_time(system_time, utcnow)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def uptime(self) -> datetime:
        """Get uptime."""
        return self.qsha_data.uptime

    def uptime_seconds(self) -> int:
        """Get uptime seconds."""
        return self.qsha_data.uptime_seconds
