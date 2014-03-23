from fabric.api import sudo, settings
from fabric.contrib.files import append
from ..aws import add_ebs
from ..server import install
from ..utils import cmd
from .base import Role


class Postgres(Role):
    def __init__(self, size_gb):
        super(Postgres, self).__init__(name='postgres')
        self.size_gb = size_gb

    def install(self):
        """ configure a server with the latest MongoDB """
        add_ebs(self.size_gb, '/var/lib/postgresql/')
        sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv ACCC4CF8')
        append('/etc/apt/sources.list.d/postgresql.list',
               'deb http://apt.postgresql.org/pub/repos/apt/ saucy-pgdg main',
               use_sudo=True)
        install(['postgresql-9.3', 'postgresql-9.3-postgis-2.1'])

    def dropdb(self, name):
        with settings(warn_only=True):
            cmd('dropdb ' + name, sudo='postgres')

    def createdb(self, name, postgis=True, drop=False):
        if drop:
            self.dropdb(name)
        cmd('createdb ' + name, sudo='postgres')
        if postgis:
            cmd('''psql {} -c 'CREATE EXTENSION postgis' '''.format(name), sudo='postgres')

    def dropuser(self, name):
        with settings(warn_only=True):
            cmd('dropuser ' + name, sudo='postgres')

    def createuser(self, name, password, drop=False):
        if drop:
            self.dropuser(name)
        cmd('''psql -c 'CREATE USER {} with SUPERUSER PASSWORD \$\${}\$\$' '''.format(
            name, password), sudo='postgres')

    _commands = ['install', 'dropdb', 'createdb', 'dropuser', 'createuser']
