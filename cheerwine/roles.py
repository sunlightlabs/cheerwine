from fabric.api import sudo, task, env
from fabric.contrib.files import append
from .utils import write_configfile, jinja
from .aws import add_ebs as _add_ebs
from .server import install as _install


def mongodb(size_gb):
    """ configure a server with the latest MongoDB """
    _add_ebs(size_gb, '/var/lib/mongodb/')
    sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv 7F0CEB10')
    append('/etc/apt/sources.list.d/mongo.list',
           'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen',
           use_sudo=True)
    _install(['mongodb-10gen'])
    sudo('restart mongodb')


def _uwsgi(settings):
    defaults = {'workers': 4, 'chmod': 666, 'no_orphans': 'true', 'master': 'true',
                'uid': env.PROJECT_NAME, 'gid': env.PROJECT_NAME,
                'home': '/projects/{}/virt/'.format(env.PROJECT_NAME)}
    lines = []
    defaults.update(settings)
    for key, val in sorted(defaults.items()):
        if isinstance(val, (tuple, list)):
            for item in val:
                lines.append('{} = {}'.format(key, item))
        else:
            lines.append('{} = {}'.format(key, val))
    return jinja.get_template('uwsgi').render(lines=lines)


def uwsgi_nginx(uwsgi_settings=None, server_name=None, port=80, locations=None):
    # install both and then remove default configured site
    _install(['nginx', 'uwsgi'])
    sudo('rm -f /etc/nginx/sites-enabled/default')

    # uwsgi stuff
    uwsgi_contents = _uwsgi(uwsgi_settings or {})
    write_configfile(uwsgi_contents, '/etc/uwsgi/apps-enabled/{}.ini'.format(env.PROJECT_NAME))

    # nginx stuff
    tmpl = jinja.get_template('nginx')
    nginx_contents = tmpl.render(port=port, server_name=server_name, locations=locations or [],
                                 project_name=env.PROJECT_NAME)
    write_configfile(nginx_contents, '/etc/nginx/sites-enabled/{}'.format(env.PROJECT_NAME))


def python():
    _install(['uwsgi-plugin-python', 'python-dev', 'python-virtualenv'])


def python3():
    _install(('python3', 'uwsgi-plugin-python3', 'python3-dev', 'python-virtualenv'))
