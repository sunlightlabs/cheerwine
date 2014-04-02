import os
from ConfigParser import SafeConfigParser
from fabric.api import env, task


@task
def config(configdir):
    env.configdir = configdir
    parser = SafeConfigParser()
    parser.read(os.path.join(configdir, 'env.ini'))
    for opt in parser.options('env'):
        setattr(env, opt.upper(), parser.get('env', opt))
        print opt
