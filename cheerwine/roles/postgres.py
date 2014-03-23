from fabric.api import sudo, env, settings
from fabric.contrib.files import append, exists
from ..aws import add_ebs
from ..server import install
from ..utils import cmd


def install(size_gb):
    """ configure a server with the latest MongoDB """
    add_ebs(size_gb, '/var/lib/postgresql/')
    sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv ACCC4CF8')
    append('/etc/apt/sources.list.d/postgresql.list',
           'deb http://apt.postgresql.org/pub/repos/apt/ saucy-pgdg main',
           use_sudo=True)
    install(['postgresql-9.3', 'postgresql-9.3-postgis-2.1'])

def dropdb(name):
    with settings(warn_only=True):
        cmd('dropdb ' + name, sudo='postgres')

def createdb(name, postgis=True, drop=False):
    if drop:
        dropdb(name)
    cmd('createdb ' + name, sudo='postgres')
    if postgis:
        cmd('''psql {} -c 'CREATE EXTENSION postgis' '''.format(name), sudo='postgres')

def dropuser(name):
    with settings(warn_only=True):
        cmd('dropuser ' + name, sudo='postgres')

def createuser(name, password, drop=False):
    if drop:
        dropuser(name)
    cmd('''psql -c 'CREATE USER {} with SUPERUSER PASSWORD \$\${}\$\$' '''.format(name, password),
        sudo='postgres')
