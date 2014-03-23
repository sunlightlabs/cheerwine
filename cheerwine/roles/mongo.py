from fabric.api import sudo, env
from fabric.contrib.files import append, exists
from ..aws import add_ebs
from ..server import install


def install(size_gb):
    """ configure a server with the latest MongoDB """
    add_ebs(size_gb, '/var/lib/mongodb/')
    sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10')
    append('/etc/apt/sources.list.d/mongo.list',
           'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen',
           use_sudo=True)
    install(['mongodb-10gen'])
    sudo('restart mongodb')
