PROGRAM_ID = '68d47554aa292d20b9bec8f7'
SHEERID_BASE_URL = 'https://services.sheerid.com'
MY_SHEERID_URL = 'https://my.sheerid.com'

HCAPTCHA_SECRET = ''
TURNSTILE_SECRET = ''
MAX_FILE_SIZE = 1024 * 1024

import sys
import os
from pathlib import Path

_BASE_DIR = None

def set_base_dir(path_str):
    global _BASE_DIR
    _BASE_DIR = Path(path_str)

def get_base_dir():
    if _BASE_DIR:
        return _BASE_DIR
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent

def get_assets_dir():
    return get_base_dir() / 'assets'

def get_templates_dir():
    if getattr(sys, 'frozen', False):
        return Path(__file__).parent / 'templates' 
    return Path(__file__).parent / 'templates'

def get_browsers_dir():
    if getattr(sys, 'frozen', False):
        return get_base_dir() / 'browsers'
    else:
        return get_base_dir() / 'browsers'

def setup_playwright_path():
    """ Sets PLAYWRIGHT_BROWSERS_PATH if bundled """
    drivers_path = get_browsers_dir()
    if drivers_path.exists():
         os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(drivers_path)

SCHOOLS = {
    '3995910': {
        'id': 3995910,
        'idExtended': '3995910',
        'name': 'Springfield High School (Springfield, OR)',
        'address': '875 7th St, Springfield, OR 97477',
        'country': 'US',
        'type': 'HIGH_SCHOOL'
    },
    '3995271': {
        'id': 3995271,
        'idExtended': '3995271',
        'name': 'Springfield High School (Springfield, OH)',
        'address': '701 E Home Rd, Springfield, OH 45503',
        'country': 'US',
        'type': 'HIGH_SCHOOL'
    },
    '3992142': {
        'id': 3992142,
        'idExtended': '3992142',
        'name': 'Springfield High School (Springfield, IL)',
        'address': '101 S Lewis St, Springfield, IL 62704',
        'country': 'US',
        'type': 'HIGH_SCHOOL'
    },
    '3996208': {
        'id': 3996208,
        'idExtended': '3996208',
        'name': 'Springfield High School (Springfield, PA)',
        'address': '49 W Leamy Ave, Springfield, PA 19064',
        'country': 'US',
        'type': 'HIGH_SCHOOL'
    },
    '4015002': {
        'id': 4015002,
        'idExtended': '4015002',
        'name': 'Springfield High School (Springfield, TN)',
        'address': '5240 Hwy 76 E, Springfield, TN 37172',
        'country': 'US',
        'type': 'HIGH_SCHOOL'
    },
    '4015001': {
        'id': 4015001,
        'idExtended': '4015001',
        'name': 'Springfield High School (Springfield, VT)',
        'address': '303 South St, Springfield, VT 05156',
        'country': 'US',
        'type': 'HIGH_SCHOOL'
    },
    '4014999': {
        'id': 4014999,
        'idExtended': '4014999',
        'name': 'Springfield High School (Springfield, LA)',
        'address': '27375 LA-42, Springfield, LA 70462',
        'country': 'US',
        'type': 'HIGH_SCHOOL'
    },
}

DEFAULT_SCHOOL_ID = '3995910'
