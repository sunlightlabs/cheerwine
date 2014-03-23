from fabric import state


def add_role(role_cls):
    for name, val in role_cls.__class__.__dict__.items():
        for name, val in role_cls.__class__.__dict__.items():
            if callable(val) and not name.startswith('_'):
                state.commands[role_cls.name + '.' + name] = getattr(role_cls, name)
