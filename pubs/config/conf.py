"""Manage the configuration file"""
import os
from os import environ
from os import getcwd
from os.path import isfile
from os.path import join
from os.path import expanduser
import platform

import configobj
import validate

from .spec import configspec


DFT_CONFIG_PATH = os.path.expanduser('~/.pubsrc')

# pylint: disable=missing-class-docstring
class ConfigurationNotFound(IOError):

    def __init__(self, path):
        # pylint: disable=super-with-arguments
        # pylint: disable=consider-using-f-string
        super(ConfigurationNotFound, self).__init__(
            "No configuration found at path {}. Maybe you need to initialize "
            "your repository with `pubs init` or specify a --config argument."
            "".format(path))


def post_process_conf(conf):
    """Do some post processing on the configuration"""
    check_conf(conf)
    if conf['main']['docsdir'] == 'docsdir://':
        conf['main']['docsdir'] = os.path.join(conf['main']['pubsdir'], 'doc')
    return conf


def load_default_conf():
    """Load the default configuration"""
    default_conf = configobj.ConfigObj(configspec=configspec)
    default_conf = post_process_conf(default_conf)
    return default_conf


# DVK def get_confpath(verify=True):
# DVK     """Return the configuration filepath
# DVK     If verify is True, verify that the file exists and exit with an error if not.
# DVK     """
# DVK     confpath = DFT_CONFIG_PATH
# DVK     if 'PUBSCONF' in os.environ:
# DVK         confpath = os.path.abspath(os.path.expanduser(os.environ['PUBSCONF']))
# DVK     if verify:
# DVK         if not os.path.isfile(confpath):
# DVK             from .. import uis
# DVK             ui = uis.get_ui()
# DVK             ui.error('configuration file not found at `{}`'.format(confpath))
# DVK             ui.exit(error_code=1)
# DVK     return confpath

def get_confpath(verify=True, path=None):
    """DVK's ver: Get `pubs` cfg filename, including looking at cwd"""
    confpathes_notfound = []
    if path is not None:
        if isfile(path):
            return path
        confpathes_notfound.append(path)
    # 1a. Search the local directory: .
    cwd = getcwd()
    fname = join(cwd, '.pubsrc')
    if isfile(fname):
        return fname
    confpathes_notfound.append(fname)
    # 1b. Search the local directory: ./.pubs
    fname = join(cwd, '.pubs/.pubsrc')
    if isfile(fname):
        return fname
    confpathes_notfound.append(fname)
    # 1c. Search the local directory: ./pubs
    fname = join(cwd, 'pubs/dot_pubsrc')
    if isfile(fname):
        return fname
    confpathes_notfound.append(fname)
    # 2. Search the user's home directory
    fname = join(expanduser('~'), '.pubsrc')
    if isfile(fname):
        return fname
    confpathes_notfound.append(fname)
    # 3. Search the environmental variable, PUBSCONF=$(DIR)/.pubsrc
    fname = environ.get('PUBSCONF')
    if fname is not None:
        if isfile(fname):
            return fname
        confpathes_notfound.append(fname)
    else:
        confpathes_notfound.append('AND environmental variable, PUBSCONF, is not set')
    files = '\n'.join(f'  * TRY pubs CONFIG FILE NAME: {fname}' for fname in confpathes_notfound)
    trythis = 'TRY:\n$ pubs init\nOR\n$ pubs init -p ./pubs'
    if verify:
        _verify_failed(confpathes_notfound)
    raise RuntimeError(f'CONFIG FILE FOR pubs NOT FOUND:\n{files}\n{trythis}')

def _verify_failed(confpathes):
    # pylint: disable=import-outside-toplevel
    # pylint: disable=invalid-name
    from .. import uis
    ui = uis.get_ui()
    pathes = '\n'.join(confpathes)
    ui.error(f'configuration file not found at any of:\n{pathes}')
    ui.exit(error_code=1)

def check_conf(conf):
    """Type check a configuration"""
    validator = validate.Validator()
    results = conf.validate(validator, copy=True)
    # pylint: disable=consider-using-f-string
    assert (results is True), '{}'.format(results)  # TODO: precise error dialog when parsing error


def load_conf(path=None):
    """Load the configuration"""
    if path is None:
        path = get_confpath(verify=True)
    if not os.path.exists(path):
        raise ConfigurationNotFound(path)
    conf = configobj.ConfigObj(path, configspec=configspec)
    conf.filename = path
    conf = post_process_conf(conf)
    return conf


def save_conf(conf, path=None):
    """Save the configuration."""
    if path is not None:
        conf.filename = path
    elif conf.filename is None:
        conf.filename = get_confpath(verify=False)
    # pylint: disable=invalid-name
    with open(conf.filename, 'wb') as f:
        conf.write(outfile=f)


def default_open_cmd():
    """Chooses the default command to open documents"""
    # pylint: disable=no-else-return
    if platform.system() == 'Darwin':
        return 'open'
    elif platform.system() == 'Linux':
        return 'xdg-open'
    elif platform.system() == 'Windows':
        return 'start'
    else:
        return None
