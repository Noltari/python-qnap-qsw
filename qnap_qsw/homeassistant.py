# -*- coding: utf-8 -*-
"""Home Assistant client for the QNAP QSW API."""

import re

from .const import (
    ATTR_ANOMALY,
    ATTR_ERROR_CODE,
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
)
from .interface import QSA, QSAException


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

    def set_firmware_condition(self, firmware_condition):
        """Set firmware/condition data."""
        if firmware_condition:
            self.condition_anomaly = firmware_condition[ATTR_RESULT][ATTR_ANOMALY]
            self.condition_message = firmware_condition[ATTR_RESULT][ATTR_MESSAGE]

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
            if system_sensor[ATTR_RESULT][ATTR_FAN1SPEED] > 0:
                self.fan_speed[0] = system_sensor[ATTR_RESULT][ATTR_FAN1SPEED]
            else:
                self.fan_speed[0] = None
            if system_sensor[ATTR_RESULT][ATTR_FAN2SPEED] > 0:
                self.fan_speed[1] = system_sensor[ATTR_RESULT][ATTR_FAN2SPEED]
            else:
                self.fan_speed[1] = None
            self.temp = system_sensor[ATTR_RESULT][ATTR_TEMP]
            self.temp_max = system_sensor[ATTR_RESULT][ATTR_TEMP_MAX]

    def set_system_time(self, system_time):
        """Set system/time data."""
        if system_time:
            self.uptime = system_time[ATTR_RESULT][ATTR_UPTIME]


class QSHA:
    """Gathers data from QNAP QSW API for Home Assistant."""

    def __init__(self, host, user, password):
        """Init QNAP QSW API for Home Assistant."""
        self.user = user
        self.password = password
        self.qsa = QSA(host)
        self.qsha_data = QSHAData()
        self._login = False

    # pylint: disable=R0912,R0915
    def async_update(self):
        """Update data from QNAP QSW API."""
        if self.login():
            error = False
            logout = False

            try:
                firmware_condition = self.qsa.get_firmware_condition()
                if firmware_condition:
                    if firmware_condition[ATTR_ERROR_CODE] == 200:
                        self.qsha_data.set_firmware_condition(firmware_condition)
                    elif firmware_condition[ATTR_ERROR_CODE] == 401:
                        logout = True
                    else:
                        error = True
            except QSAException:
                error = True

            try:
                firmware_info = self.qsa.get_firmware_info()
                if firmware_info:
                    if firmware_info[ATTR_ERROR_CODE] == 200:
                        self.qsha_data.set_firmware_info(firmware_info)
                    elif firmware_info[ATTR_ERROR_CODE] == 401:
                        logout = True
                    else:
                        error = True
            except QSAException:
                error = True

            try:
                firmware_update = self.qsa.get_firmware_update_check()
                if firmware_update:
                    if firmware_update[ATTR_ERROR_CODE] == 200:
                        self.qsha_data.set_firmware_update(firmware_update)
                    elif firmware_update[ATTR_ERROR_CODE] == 401:
                        logout = True
                    else:
                        error = True
            except QSAException:
                error = True

            try:
                system_board = self.qsa.get_system_board()
                if system_board:
                    if system_board[ATTR_ERROR_CODE] == 200:
                        self.qsha_data.set_system_board(system_board)
                    elif system_board[ATTR_ERROR_CODE] == 401:
                        logout = True
                    else:
                        error = True
            except QSAException:
                error = True

            try:
                system_sensor = self.qsa.get_system_sensor()
                if system_sensor:
                    if system_sensor[ATTR_ERROR_CODE] == 200:
                        self.qsha_data.set_system_sensor(system_sensor)
                    elif system_sensor[ATTR_ERROR_CODE] == 401:
                        logout = True
                    else:
                        error = True
            except QSAException:
                error = True

            try:
                system_time = self.qsa.get_system_time()
                if system_time:
                    if system_time[ATTR_ERROR_CODE] == 200:
                        self.qsha_data.set_system_time(system_time)
                    elif system_time[ATTR_ERROR_CODE] == 401:
                        logout = True
                    else:
                        error = True
            except QSAException:
                error = True

            if logout:
                self.logout()

            if logout:
                raise LoginError("QNAP QSW API returned unauthorized status")
            if error:
                raise ConnectionError("QNAP QSW API returned unknown error")

            return not (error or logout)

        return False

    def condition_anomaly(self) -> bool:
        """Condition anomaly."""
        return self.qsha_data.condition_anomaly

    def condition_message(self) -> str:
        """Condition message."""
        return self.qsha_data.condition_message

    def config_url(self) -> str:
        """Configuration URL."""
        return self.qsa.config_url()

    def data(self):
        """Data Dict."""
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
        }

        if self.fan_count() > 0:
            _data[DATA_FAN1_SPEED] = self.fan_speed(0)
        if self.fan_count() > 1:
            _data[DATA_FAN2_SPEED] = self.fan_speed(1)

        return _data

    def fan_count(self) -> int:
        """Number of fans."""
        fans = self.qsha_data.fan_speed
        count = 0
        for fan in fans:
            if fan:
                count = count + 1
        return count

    def fan_speed(self, idx) -> int:
        """Fan speed."""
        if idx > len(self.qsha_data.fan_speed):
            return None
        return self.qsha_data.fan_speed[idx]

    def firmware(self) -> str:
        """Firmware."""
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
        """MAC address."""
        return self.qsha_data.mac

    def model(self) -> str:
        """Product model."""
        return self.qsha_data.model

    def product(self) -> str:
        """Product name."""
        return self.qsha_data.product

    def reboot(self) -> bool:
        """Reboot QNAP QSW switch."""
        if self.login():
            response = self.qsa.post_system_command(ATTR_REBOOT)
            if (
                response
                and response[ATTR_ERROR_CODE] == 200
                and not response[ATTR_RESULT]
            ):
                return True

        return False

    def serial(self) -> str:
        """Serial number."""
        _serial = self.qsha_data.serial
        if _serial:
            return re.sub(r"[\W_]+", "", _serial)
        return None

    def temp(self) -> int:
        """Current temperature."""
        return self.qsha_data.temp

    def temp_max(self) -> int:
        """Max temperature."""
        return self.qsha_data.temp_max

    def update(self) -> bool:
        """Firmware update."""
        return self.qsha_data.update

    def update_version(self) -> str:
        """Firmware update version."""
        return self.qsha_data.update_version

    def uptime(self) -> int:
        """Uptime."""
        return self.qsha_data.uptime
