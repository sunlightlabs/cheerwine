# Cheerwine

a utility library for common fabric tasks

it is just a little better than [sundrop](https://github.com/sunlightlabs/sundrop)


## Public Interface

Environment Variables:

* env.PROJECT_NAME
* env.CMD_LOCAL


### cheerwine.server - General Server Utils

Commands:

* set_hosts(hostname, peers)
* add_superuser(user, directory)
* upgrade()
* install(packages)
* install_base(additional)
* checkout(dirname, gitrepo, branch='master')
* update(dirname)


### cheerwine.roles - Configuration of server into various roles

Commands:

* mongodb.install(size_gb)
* postgres.install(size_gb)
* postgres.dropdb(name)
* postgres.createdb(name, postgis=True, drop=False)
* postgres.dropuser(name)
* postgres.createuser(name, password, drop=False)
* python.restart_nginx()
* python.restart_uwsgi()
* python.uwsgi_nginx(module, settings, pythonpath, env_vars, processes, uwsgi-extras, server_name, port=80, locations=None)
* python.python
* python.python3

### cheerwine.aws - Amazon Web Services

Environment Variables:

* env.AWS_KEY
* env.AWS_SECRET

Commands:

* add_ebs(size_gb, path, iops=None)
* add_project_ebs(size, projname, iops=None)



### cheerwine.utils - General Utils

Commands:

* copy_dir(local, remote, user=None)
* write_configfile(remote_path, content=None, filename=None)
