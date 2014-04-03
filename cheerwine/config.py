import os
from ConfigParser import SafeConfigParser
from fabric.api import env, task


def filename(name):
    filenames = (os.path.join(env.configdir, env.mode, name), os.path.join(env.configdir, name))
    for fn in filenames:
        if os.path.exists(fn):
            return fn
    raise ValueError('file "{}" not found.  tried {} and {}'.format(name, *filenames))


def load_env():
    parser = SafeConfigParser()
    parser.read(filename('env.ini'))
    for opt in parser.options('env'):
        setattr(env, opt, parser.get('env', opt))


@task
def production():
    env.configdir = os.environ.get('CHEERWINE_CONFIG_DIR')
    env.mode = 'production'
    load_env()


@task
def staging():
    env.configdir = os.environ.get('CHEERWINE_CONFIG_DIR')
    env.mode = 'staging'
    load_env()
