import os
from fabric.api import task, env
from ConfigParser import SafeConfigParser
from .utils import assert_configdir


def _load_env():
    parser = SafeConfigParser()
    parser.read(os.path.join(assert_configdir(), 'env.ini'))
    for opt in parser.options('env'):
        setattr(env, opt, parser.get('env', opt))


@task
def production():
    env.configdir = os.environ.get('CHEERWINE_CONFIG_PATH')
    env.mode = 'production'
    _load_env()


@task
def staging():
    env.configdir = os.environ.get('CHEERWINE_CONFIG_PATH')
    env.mode = 'staging'
    _load_env()
