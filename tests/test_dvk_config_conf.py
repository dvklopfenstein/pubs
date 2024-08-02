"""Test DVK's changes to pubs/config/conf.py"""

import os
from os.path import expanduser

from sys import stdout
from sys import stderr

import monkeypatch
from tempfile import TemporaryDirectory

# https://docs.pytest.org/en/latest/reference/reference.html#_pytest.monkeypatch.monkeypatch
from pytest import MonkeyPatch
#from pytest import tmp_path

from pubs.config.conf import get_confpath

def test_get_confpath():
    """Test DVK's changes to pubs/config/conf.py"""
    with MonkeyPatch().context() as mptch:
        try:
            mptch.setattr(os.path, 'expanduser', lambda: '/tmp')
            print(expanduser('~'))
            print(f'get_confpath({get_confpath()})')
            #_create_env()
        except SystemExit as err:
            assert err.code == 1, f'FATAL: EXPECTED sys.exit(1); ACTUAL sys.exit({err})'
        assert 'FATAL: EXPECTED NO .pubsrc TO BE FOUND'
    stdout.flush() 
    stderr.flush() 
    print('TEST PASSED')

def _create_env():
    """Create a mock environment"""
    tdir = tmp_path()
    print(tdir)


if __name__ == '__main__':
    test_get_confpath()
