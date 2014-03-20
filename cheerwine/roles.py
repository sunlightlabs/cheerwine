from fabric.api import sudo, task, env
from fabric.contrib.files import append, exists
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


def _uwsgi(module, settings_module, pythonpath, env_vars, processes, extras):
    settings = {'master': 'true',
                'vacuum': 'true',
                'chmod-socket': '666',
                'module': module,
                'pythonpath': pythonpath,
                'env': env_vars,
                'processes': processes,
                # log-5xx, log-slow, disable-logging, log-x-forwarded-for, reload-on-rss
               }
    lines = []
    settings.update(extras)
    for key, val in sorted(settings.items()):
        if isinstance(val, (tuple, list)):
            for item in val:
                lines.append('{} = {}'.format(key, item))
        else:
            lines.append('{} = {}'.format(key, val))
    return jinja.get_template('uwsgi').render(user=env.PROJECT_NAME, settings=settings_module,
                                              lines=lines)


def restart_nginx():
    sudo('/etc/init.d/nginx restart')


def restart_uwsgi():
    sudo('/etc/init.d/uwsgi restart {0}'.format(env.PROJECT_NAME))


def uwsgi_nginx(module, settings=None, pythonpath=None, env_vars=None, processes=4,
                uwsgi_extras=None, server_name=None, port=80, locations=None):
    # install both and then remove default configured site
    _install(['nginx', 'uwsgi'])
    sudo('rm -f /etc/nginx/sites-enabled/default')

    # uwsgi stuff
    uwsgi_contents = _uwsgi(module=module, settings_module=settings,
                            pythonpath=pythonpath or [], env_vars=env_vars or [],
                            processes=processes, extras=uwsgi_extras or {})
    write_configfile('/etc/uwsgi/apps-enabled/{}.ini'.format(env.PROJECT_NAME),
                     content=uwsgi_contents)
    restart_uwsgi()

    # nginx stuff
    tmpl = jinja.get_template('nginx')
    nginx_contents = tmpl.render(port=port, server_name=server_name, locations=locations or [],
                                 project_name=env.PROJECT_NAME)
    write_configfile('/etc/nginx/sites-enabled/{}'.format(env.PROJECT_NAME),
                     content=nginx_contents)
    restart_nginx()


def python():
    _install(['uwsgi-plugin-python', 'python-dev', 'python-virtualenv'])


def python3():
    _install(('python3', 'uwsgi-plugin-python3', 'python3-dev', 'python-virtualenv'))
