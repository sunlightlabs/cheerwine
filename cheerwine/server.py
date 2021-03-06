from fabric.api import run, prompt, sudo, hide, abort, settings
from fabric.colors import red
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


def upgrade():
    """ do a server upgrade """
    sudo('aptitude update')
    sudo('aptitude upgrade -y')


def install(packages):
    """ install a package """
    sudo('aptitude install -y -q {0}'.format(' '.join(packages)))


def install_base(additional):
    upgrade()
    install(('xfsprogs', 'build-essential', 'git', 'mercurial') + tuple(additional))


def write_cron(cronlines, proj):
    with settings(hide('running', 'stderr', 'stdout', 'warnings'), warn_only=True):
        sudo('crontab -u {0} -l > /tmp/crondump-{0}'.format(proj))
    write_configfile('/tmp/crondump-' + proj, cronlines + '\n')
    sudo('cat /tmp/crondump-{0} | sudo crontab -u {0} -'.format(proj))
