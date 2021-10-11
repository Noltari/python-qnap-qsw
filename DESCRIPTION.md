python-qnap-qsw is a Python module implementing an interface to the QNAP QSW API.  
It allows a user to gather all the information from a QNAP switch.

This package has been developed to be used with https://home-assistant.io/ but it can be used in other contexts.

Disclaimer
----------

python-qnap-qsw was created for my own use, and for others who may wish to experiment with personal Internet of Things systems.

I have no connection with QNAP. I receive no help (financial or otherwise) from QNAP, and have no business interest with them.

This software is provided without warranty, according to the GNU Public Licence version 2, and should therefore not be used where it may endanger life, financial stakes, or cause discomfort and inconvenience to others.

Usage
-----

>>> from qnap_qsw.interface import QSA
_qsa = QSA(host="host/url")
_qsa.login(user="admin", password="password")
_qsa.get_system_board()
_qsa.get_system_sensor()
_qsa.logout()

>>> from pprint import pprint
from qnap_qsw.homeassistant import QSHA
_qsha = QSHA(host="host/url", user="admin", password="password")
_qsha.async_update()
pprint(vars(_qsha.data))
_qsha.reboot()
