from fabric.api import sudo
from fabric.contrib.files import append
from ..aws import add_ebs
from ..server import install
from .base import Role


class Mongo(Role):

    def __init__(self, size_gb):
        super(Mongo, self).__init__(name='mongo')
        self.size_gb = size_gb

    def install(self):
        """ configure a server with the latest MongoDB """
        add_ebs(self.size_gb, '/var/lib/mongodb/')
        sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10')
        append('/etc/apt/sources.list.d/mongo.list',
               'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen',
               use_sudo=True)
        install(['mongodb-10gen'])
        sudo('restart mongodb')
