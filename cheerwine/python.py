from fabric.api import sudo, env, task


def make_venv():
    """ make a virtual environment """
    sudo('virtualenv /projects/{}/virt'.format(env.PROJECT_NAME), user=env.PROJECT_NAME)


def pip_install(package):
    """ install something into the virtualenv """
    sudo('source ~{}/virt/bin/activate && pip install -r {}'.format(env.PROJECT_NAME, package))


def django(command):
    """ run a django command """
    command = '/projects/{projname}/virt/bin/python `find /projects/{projname}/src/ -name manage.py` {0}'.format(command, **env)
    if env.server_type == 'staging' and 'staging_settings' in env.proj:
        command += ' --settings={0}'.format(env.proj['staging_settings'])
    sudo(command)


def collectstatic():
    """ django collectstatic command """
    django('collectstatic')
