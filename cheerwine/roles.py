from fabric.api import sudo, task, env
from fabric.contrib.files import append
from .utils import write_configfile
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
    defaults.update(settings)
    lines = ['[uwsgi]']
    for key, val in sorted(defaults.items()):
        if isinstance(val, (tuple, list)):
            for item in val:
                lines.append('{} = {}'.format(key, item))
        else:
            lines.append('{} = {}'.format(key, val))
    return '\n'.join(lines)

def _nginx(server_name=None, port=80, locations=''):
    if locations:
        locations = ["\tlocation {} { root {}; }".format(loc, root) for loc, root in locations]
        locations = '\n'.join(locations)

    template = """server {
    listen {port};
    server_name _;
    rewrite ^ $scheme://{server_name}$uri permanent;
}

server {
    listen {port};
    server_name {server_name};

    location / {
        uwsgi_pass unix:///projects/{project_name}/data/uwsgi.sock;
        include uwsgi_params;
    }

    {locations}

    access_log /projects/{project_name}/logs/access.log combined;
    error_log /projects/{project_name}/logs/error.log;
}"""
    return template.format(port=port, server_name=server_name, locations=locations,
                           project_name=env.PROJECT_NAME)


def uwsgi(uwsgi=None):
    if not uwsgi:
        uwsgi = {}
    uwgi_contents = _uwsgi(uwsgi)
    write_configfile(uwgi_contents, '/etc/uwsgi/apps-enabled/{}.ini'.format(env.PROJECT_NAME))


def web():
    """ configure a server as a web server """
    _install(['nginx', 'uwsgi', 'uwsgi-plugin-python'])
    # remove default configured site
    sudo('rm /etc/nginx/sites-enabled/default')
