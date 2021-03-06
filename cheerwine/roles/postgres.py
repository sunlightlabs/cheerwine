from fabric.api import sudo, settings
from fabric.contrib.files import append
from ..server import install
from ..utils import add_ebs, is_localhost
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
        if not is_localhost():
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
                sudo('dropdb ' + name, user='postgres')
        sudo('createdb ' + name, user='postgres')
        if self.postgis:
            sudo('''psql {} -c 'CREATE EXTENSION postgis' '''.format(name), user='postgres')

    def _createuser(self, name, drop=False):
        if drop:
            with settings(warn_only=True):
                sudo('dropuser ' + name, user='postgres')
        sudo('createuser -P -s ' + name, user='postgres')

    def createdb(self):
        """ create user and db """
        self._createdb(self.dbname, drop=True)
        self._createuser(self.dbuser, drop=True)
