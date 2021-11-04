# -*- coding: utf-8 -*-
"""Home Assistant client for the QNAP QSW API."""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from typing import List

from .const import (
    ATTR_ANOMALY,
    ATTR_DOWNLOAD_URL,
    ATTR_ERROR_CODE,
    ATTR_ERROR_MESSAGE,
    ATTR_FAN1SPEED,
    ATTR_FAN2SPEED,
    ATTR_KEY,
    ATTR_LINK,
    ATTR_MAC,
    ATTR_MESSAGE,
    ATTR_MODEL,
    ATTR_NEWER,
    ATTR_NUM_PORTS,
    ATTR_NUMBER,
    ATTR_PRODUCT,
    ATTR_PUB_DATE,
    ATTR_REBOOT,
    ATTR_RESULT,
    ATTR_SERIAL,
    ATTR_TEMP,
    ATTR_TEMP_MAX,
    ATTR_UPTIME,
    ATTR_VAL,
    ATTR_VERSION,
    DATA_CONDITION_ANOMALY,
    DATA_CONDITION_MESSAGE,
    DATA_CONFIG_URL,
    DATA_FAN1_SPEED,
    DATA_FAN2_SPEED,
    DATA_FAN_COUNT,
    DATA_FIRMWARE_CURRENT_VERSION,
    DATA_FIRMWARE_DATETIME,
    DATA_FIRMWARE_DATETIME_ISOFORMAT,
    DATA_FIRMWARE_DOWNLOAD_URL,
    DATA_FIRMWARE_LATEST_VERSION,
    DATA_FIRMWARE_UPDATE,
    DATA_PORTS_ACTIVE,
    DATA_PORTS_COUNT,
    DATA_SYSTEM_MAC_ADDR,
    DATA_SYSTEM_MODEL,
    DATA_SYSTEM_PRODUCT,
    DATA_SYSTEM_SERIAL,
    DATA_TEMPERATURE_CURRENT,
    DATA_TEMPERATURE_MAXIMUM,
    DATA_UPTIME_DATETIME,
    DATA_UPTIME_DATETIME_ISOFORMAT,
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


@dataclass
class QSHADataCondition:
    """Class for keeping track of QSW condition."""

    anomaly: bool = False
    message: str = None

    def data(self) -> dict:
        """Get data Dict."""
        return {
            DATA_CONDITION_ANOMALY: self.anomaly,
            DATA_CONDITION_MESSAGE: self.message,
        }


@dataclass
class QSHADataFans:
    """Class for keeping track of QSW fans."""

    fan_count: int = None
    fan_speed: List[int] = None

    def data(self) -> dict:
        """Get data Dict."""
        _count = self.count()
        _data = {
            DATA_FAN_COUNT: _count,
        }
        if _count > 0:
            _data[DATA_FAN1_SPEED] = self.speed(0)
        if _count > 1:
            _data[DATA_FAN2_SPEED] = self.speed(1)
        return _data

    def count(self) -> int:
        """Get number of fans."""
        _count = 0
        if self.fan_speed:
            for fan in self.fan_speed:
                if fan:
                    _count = _count + 1
        return _count

    def set_speed(self, idx, speed) -> int:
        """Set fan speed."""
        if not self.fan_speed:
            self.fan_speed = [None] * 2
        if idx < len(self.fan_speed):
            self.fan_speed[idx] = speed

    def speed(self, idx) -> int:
        """Get fan speed."""
        if idx > len(self.fan_speed):
            return None
        return self.fan_speed[idx]


@dataclass
class QSHADataFirmware:
    """Class for keeping track of QSW firmware."""

    current_version: str = None
    datetime: datetime = None
    download_url: str = None
    latest_version: str = None
    update: bool = False

    def data(self) -> dict:
        """Get data Dict."""
        _data = {
            DATA_FIRMWARE_CURRENT_VERSION: self.current_version,
            DATA_FIRMWARE_DATETIME: self.datetime,
            DATA_FIRMWARE_DOWNLOAD_URL: self.download_url,
            DATA_FIRMWARE_LATEST_VERSION: self.latest_version,
            DATA_FIRMWARE_UPDATE: self.update,
        }
        if self.datetime:
            _data[DATA_FIRMWARE_DATETIME_ISOFORMAT] = self.datetime.isoformat()
        else:
            _data[DATA_FIRMWARE_DATETIME_ISOFORMAT] = None
        return _data


@dataclass
class QSHADataPorts:
    """Class for keeping track of QSW ports."""

    active: int = None
    count: int = None

    def data(self) -> dict:
        """Get data Dict."""
        return {
            DATA_PORTS_ACTIVE: self.active,
            DATA_PORTS_COUNT: self.count,
        }


@dataclass
class QSHADataSystem:
    """Class for keeping track of QSW system."""

    mac_addr: str = None
    model: str = None
    product: str = None
    serial: str = None

    def data(self) -> dict:
        """Get data Dict."""
        return {
            DATA_SYSTEM_MAC_ADDR: self.mac_addr,
            DATA_SYSTEM_MODEL: self.model,
            DATA_SYSTEM_PRODUCT: self.product,
            DATA_SYSTEM_SERIAL: self.serial_str(),
        }

    def serial_str(self) -> str:
        """Get serial number."""
        serial = self.serial
        if serial:
            return re.sub(r"[\W_]+", "", serial)
        return None


@dataclass
class QSHADataTemperature:
    """Class for keeping track of QSW temperature."""

    current: int = None
    maximum: int = None

    def data(self) -> dict:
        """Get data Dict."""
        return {
            DATA_TEMPERATURE_CURRENT: self.current,
            DATA_TEMPERATURE_MAXIMUM: self.maximum,
        }


@dataclass
class QSHADataUptime:
    """Class for keeping track of QSW uptime."""

    datetime: datetime = None
    seconds: int = None

    def data(self) -> dict:
        """Get data Dict."""
        _data = {
            DATA_UPTIME_DATETIME: self.datetime,
            DATA_UPTIME_SECONDS: self.seconds,
        }
        if self.datetime:
            _data[DATA_UPTIME_DATETIME_ISOFORMAT] = self.datetime.isoformat()
        else:
            _data[DATA_UPTIME_DATETIME_ISOFORMAT] = None
        return _data


@dataclass
class QSHAData:
    """Stores data from QNAP QSW API for Home Assistant."""

    condition = QSHADataCondition()
    fans = QSHADataFans()
    firmware = QSHADataFirmware()
    ports = QSHADataPorts()
    system = QSHADataSystem()
    temperature = QSHADataTemperature()
    uptime = QSHADataUptime()

    def data(self) -> dict:
        """Get data Dict."""
        _data = {}
        _data.update(self.condition.data())
        _data.update(self.fans.data())
        _data.update(self.firmware.data())
        _data.update(self.ports.data())
        _data.update(self.system.data())
        _data.update(self.uptime.data())
        _data.update(self.temperature.data())
        return _data

    def set_firmware_condition(self, firmware_condition):
        """Set firmware/condition data."""
        self.condition.anomaly = firmware_condition[ATTR_RESULT][ATTR_ANOMALY]
        _msg = firmware_condition[ATTR_RESULT][ATTR_MESSAGE]
        if self.condition.anomaly and _msg and len(_msg) > 0:
            self.condition.message = _msg
        else:
            self.condition.message = None

    def set_firmware_info(self, firmware_info):
        """Set firmware/info data."""
        self.firmware.current_version = (
            f"{firmware_info[ATTR_RESULT][ATTR_VERSION]}."
            f"{firmware_info[ATTR_RESULT][ATTR_NUMBER]}"
        )
        self.firmware.datetime = datetime.strptime(
            firmware_info[ATTR_RESULT][ATTR_PUB_DATE], "%a, %d %b %Y %H:%M:%S %z"
        )

    def set_firmware_update(self, firmware_update):
        """Set firmware/update data."""
        self.firmware.update = firmware_update[ATTR_RESULT][ATTR_NEWER]
        if self.firmware.update:
            self.firmware.latest_version = (
                f"{firmware_update[ATTR_RESULT][ATTR_VERSION]}."
                f"{firmware_update[ATTR_RESULT][ATTR_NUMBER]}"
            )
        else:
            self.firmware.latest_version = None

        download_url = firmware_update[ATTR_RESULT][ATTR_DOWNLOAD_URL]
        if isinstance(download_url, list):
            self.firmware.download_url = download_url[0]
        else:
            self.firmware.download_url = download_url

    def set_ports_status(self, ports_status):
        """Set ports/status data."""
        active = 0
        for port in ports_status[ATTR_RESULT]:
            if int(port[ATTR_KEY]) <= self.ports.count and port[ATTR_VAL][ATTR_LINK]:
                active = active + 1
        self.ports.active = active

    def set_system_board(self, system_board):
        """Set system/board data."""
        self.system.mac_addr = system_board[ATTR_RESULT][ATTR_MAC]
        self.system.model = system_board[ATTR_RESULT][ATTR_MODEL]
        self.ports.count = system_board[ATTR_RESULT][ATTR_NUM_PORTS]
        self.system.product = system_board[ATTR_RESULT][ATTR_PRODUCT]
        self.system.serial = system_board[ATTR_RESULT][ATTR_SERIAL]

    def set_system_sensor(self, system_sensor):
        """Set system/sensor data."""
        if system_sensor[ATTR_RESULT][ATTR_FAN1SPEED] >= 0:
            self.fans.set_speed(0, system_sensor[ATTR_RESULT][ATTR_FAN1SPEED])
        else:
            self.fans.set_speed(0, None)
        if system_sensor[ATTR_RESULT][ATTR_FAN2SPEED] >= 0:
            self.fans.set_speed(1, system_sensor[ATTR_RESULT][ATTR_FAN1SPEED])
        else:
            self.fans.set_speed(1, None)
        self.temperature.current = system_sensor[ATTR_RESULT][ATTR_TEMP]
        self.temperature.maximum = system_sensor[ATTR_RESULT][ATTR_TEMP_MAX]

    def set_system_time(self, system_time, utcnow):
        """Set system/time data."""
        self.uptime.seconds = system_time[ATTR_RESULT][ATTR_UPTIME]
        uptime = (utcnow - timedelta(seconds=self.uptime.seconds)).replace(
            microsecond=0, tzinfo=timezone.utc
        )
        if self.uptime.datetime:
            if abs((uptime - self.uptime.datetime).total_seconds()) > UPTIME_DELTA:
                self.uptime.datetime = uptime
        else:
            self.uptime.datetime = uptime


class QSHA:
    """Gathers data from QNAP QSW API for Home Assistant."""

    def __init__(self, host, user, password):
        """Init QNAP QSW API for Home Assistant."""
        self.user = user
        self.password = password
        self.qsa = QSA(host)
        self.qsha_data = QSHAData()
        self._login = False

    def api_alive(self) -> bool:
        """Check if QNAP QSW API is alive."""
        try:
            result = self.qsa.get_live()
            return bool(
                result
                and (result[ATTR_ERROR_CODE] == HTTPStatus.OK)
                and (result[ATTR_RESULT] is None)
            )
        except QSAException:
            return False

    def api_response(self, cmd, result) -> bool:
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

    def config_url(self) -> str:
        """Get configuration URL."""
        return self.qsa.config_url()

    def data(self) -> dict:
        """Get data Dict."""
        _data = self.qsha_data.data()
        _data.update({DATA_CONFIG_URL: self.config_url()})
        return _data

    def login(self) -> bool:
        """Login."""
        if self._login:
            result = self.qsa.get_users_verification()
            if result[ATTR_ERROR_CODE] == HTTPStatus.UNAUTHORIZED:
                self.logout()
        if not self._login:
            if self.qsa.login(self.user, self.password):
                self._login = True
        return self._login

    def logout(self):
        """Logout."""
        if self._login:
            self.qsa.logout()
        self._login = False

    def reboot(self) -> bool:
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

    def update_firmware_condition(self) -> bool:
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

    def update_firmware_info(self) -> bool:
        """Update firmware/info from QNAP QSW API."""
        try:
            firmware_info = self.qsa.get_firmware_info()
            if firmware_info and self.api_response("firmware/info", firmware_info):
                self.qsha_data.set_firmware_info(firmware_info)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_firmware_update_check(self) -> bool:
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

    def update_ports_status(self) -> bool:
        """Update ports/status from QNAP QSW API."""
        try:
            ports_status = self.qsa.get_ports_status()
            if ports_status and self.api_response("ports/status", ports_status):
                self.qsha_data.set_ports_status(ports_status)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_system_board(self) -> bool:
        """Update system/board from QNAP QSW API."""
        try:
            system_board = self.qsa.get_system_board()
            if system_board and self.api_response("system/board", system_board):
                self.qsha_data.set_system_board(system_board)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_system_sensor(self) -> bool:
        """Update system/sensor from QNAP QSW API."""
        try:
            system_sensor = self.qsa.get_system_sensor()
            if system_sensor and self.api_response("system/sensor", system_sensor):
                self.qsha_data.set_system_sensor(system_sensor)
                return True
            return False
        except QSAException as err:
            raise ConnectionError from err

    def update_system_time(self) -> bool:
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
