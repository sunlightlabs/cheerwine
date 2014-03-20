from fabric.api import env, run, prompt, sudo, hide, open_shell, abort, cd, task
from fabric.colors import red
from fabric.contrib.files import append, exists
from .utils import _info, _good, copy_dir, write_configfile


def _etc_hosts(hostname, peers):
    contents = """127.0.0.1 localhost
# The following lines are desirable for IPv6 capable hosts
::1 ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
# the hostname and its peers
127.0.0.1 {0}\n""".format(hostname)
    if peers:
        for name, ip in sorted(peers.items()):
            contents += '{0} {1}\n'.format(ip, name)
    return contents


def set_hosts(hostname, peers=None):
    """ set hostname and place peers in /etc/hosts """
    with hide('running', 'stdout'):
        curhost = run('cat /etc/hostname')
    _info('setting hostname...')
    if curhost != hostname:
        if prompt('changing hostname from {0} to {1}? [y/n]'.format(curhost, hostname)) != 'y':
            abort(red('aborting!'))
        else:
            sudo('echo "{0}" > /etc/hostname'.format(hostname))
            sudo('start hostname')
    else:
        _good('already set!')
    contents = _etc_hosts(hostname, peers or [])
    write_configfile('/etc/hosts', content=contents)


def add_superuser(user, directory):
    """ create a new user with sudo rights """
    sudo('useradd {0} --base-dir /etc/skel --home-dir /home/{0} --create-home '
         '--shell /bin/bash --groups admin'.format(user))
    sudo('passwd {0}'.format(user))
    copy_dir(directory, '/home/{0}/'.format(user), user)


# KILL?
def connect(hostname):
    """ open a connection to the server in question """
    server = env.SERVERS[hostname]
    env.host_string = 'ubuntu@' + server['public_dns']
    open_shell()


def upgrade():
    """ do a server upgrade """
    sudo('aptitude update')
    sudo('aptitude upgrade -y')

def install(packages):
    """ install a package """
    sudo('aptitude install -y {0}'.format(' '.join(packages)))


def install_base(additional):
    upgrade()
    install(('xfsprogs', 'build-essential', 'git', 'mercurial') + tuple(additional))


def checkout(dirname, gitrepo, branch='master'):
    """ check code out into project directory """
    dirname = '~{}/src/{}'.format(env.PROJECT_NAME, dirname)
    if exists(dirname):
        _info('directory {} already exists'.format(dirname))
    else:
        with cd('~{}/src'.format(env.PROJECT_NAME)):
            sudo('git clone -b {} {} {}'.format(branch, gitrepo, dirname), user=env.PROJECT_NAME)


def update(dirname):
    """ update git repository """
    with cd('~{}/src/{}'.format(env.PROJECT_NAME, dirname)):
        sudo('git pull', user=env.PROJECT_NAME)
