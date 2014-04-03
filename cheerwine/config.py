import os
from ConfigParser import SafeConfigParser
from fabric.api import env, task, abort
from .utils import _bad

def _assert_configdir():
    if not getattr(env, 'configdir', None):
        _bad('config directory is not set, call production or staging')
        abort('no config directory set')
    return env.configdir


def load_env():
    parser = SafeConfigParser()
    parser.read(os.path.join(_assert_configdir(), 'env.ini'))
    for opt in parser.options('env'):
        setattr(env, opt, parser.get('env', opt))


@task
def production():
    env.configdir = os.environ.get('CHEERWINE_CONFIG_PATH')
    env.mode = 'production'
    load_env()


@task
def staging():
    env.configdir = os.environ.get('CHEERWINE_CONFIG_PATH')
    env.mode = 'staging'
    load_env()
