from fabric.api import sudo, env, task
from fabric.contrib.files import exists
from .utils import _info


def make_venv(python3=False):
    """ make a virtual environment """
    dirname = '/projects/{}/virt'.format(env.PROJECT_NAME)
    if exists(dirname):
        _info('directory {} already exists'.format(dirname))
    else:
        cmd = 'virtualenv ' + dirname
        if python3:
            cmd += ' -p python3'
        sudo(cmd, user=env.PROJECT_NAME)


def pip_install(package):
    """ install something into the virtualenv """
    sudo('source ~{}/virt/bin/activate && pip install {}'.format(env.PROJECT_NAME, package))


def django(command):
    """ run a django command """
    command = '/projects/{projname}/virt/bin/python `find /projects/{projname}/src/ -name manage.py` {0}'.format(command, **env)
    if env.server_type == 'staging' and 'staging_settings' in env.proj:
        command += ' --settings={0}'.format(env.proj['staging_settings'])
    sudo(command)


def collectstatic():
    """ django collectstatic command """
    django('collectstatic')
