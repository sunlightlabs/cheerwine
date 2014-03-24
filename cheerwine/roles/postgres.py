from fabric.api import sudo, settings, env
from fabric.contrib.files import append
from ..aws import add_ebs
from ..server import install
from ..utils import cmd
from .base import Role


class Postgres(Role):
    def __init__(self, size_gb, dbname, dbuser, postgis=False):
        super(Postgres, self).__init__(name='postgres')
        self.size_gb = size_gb
        self.dbname = dbname
        self.dbuser = dbuser
        self.postgis = postgis

    def install(self):
        """ configure a server with the latest MongoDB """
        add_ebs(self.size_gb, '/var/lib/postgresql/')
        sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv ACCC4CF8')
        append('/etc/apt/sources.list.d/postgresql.list',
               'deb http://apt.postgresql.org/pub/repos/apt/ saucy-pgdg main',
               use_sudo=True)
        sudo('apt-get update')
        install(['postgresql-9.3', 'postgresql-9.3-postgis-2.1', 'postgresql-server-dev-9.3'])

    def _createdb(self, name, drop=False):
        if drop:
            with settings(warn_only=True):
                cmd('dropdb ' + name, sudo='postgres')
        cmd('createdb ' + name, sudo='postgres')
        if self.postgis:
            cmd('''psql {} -c 'CREATE EXTENSION postgis' '''.format(name), sudo='postgres')

    def _createuser(self, name, drop=False):
        if drop:
            with settings(warn_only=True):
                cmd('dropuser ' + name, sudo='postgres')
        cmd('createuser -P -s ' + name, sudo='postgres')

    def createdb(self):
        self._createdb(self.dbname, drop=True)
        self._createuser(self.dbuser, drop=True)
