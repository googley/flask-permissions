try:
    from .core import db
except ImportError:
    raise Exception(
        'Permissions app must be initialized before importing models')

from passlib.apps import custom_app_context as pwd_context
from sqlalchemy.ext.associationproxy import association_proxy
from .utils import is_sequence


def _role_find_or_create(r):
    role = Role.query.filter_by(name=r).first()
    if not(role):
        role = Role(name=r)
        db.session.add(role)
    return role

def _container_find_or_create(c):
    container = Container.query.filter_by(name=c).first()
    if not(container):
        container = Container(name=c)
        db.session.add(container)
    return container


user_role_table = db.Table('fp_user_role',
                           db.Column(
                               'user_id', db.Integer, db.ForeignKey('fp_user.id')),
                           db.Column(
                           'role_id', db.Integer, db.ForeignKey('fp_role.id'))
                           )

user_container_table = db.Table('fp_user_container',
                           db.Column(
                               'user_id', db.Integer, db.ForeignKey('fp_user.id')),
                           db.Column(
                           'container_id', db.Integer, db.ForeignKey('fp_container.id'))
                           )

role_ability_table = db.Table('fp_role_ability',
                              db.Column(
                                  'role_id', db.Integer, db.ForeignKey('fp_role.id')),
                              db.Column(
                              'ability_id', db.Integer, db.ForeignKey('fp_ability.id'))
                              )


class Role(db.Model):

    """
    Subclass this for your roles
    """
    __tablename__ = 'fp_role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    abilities = db.relationship(
        'Ability', secondary=role_ability_table, backref='roles')

    def __init__(self, name):
        self.name = name.lower()

    def add_abilities(self, *abilities):
        for ability in abilities:
            existing_ability = Ability.query.filter_by(
                name=ability).first()
            if not existing_ability:
                existing_ability = Ability(ability)
                db.session.add(existing_ability)
                db.session.commit()
            self.abilities.append(existing_ability)

    def remove_abilities(self, *abilities):
        for ability in abilities:
            existing_ability = Ability.query.filter_by(name=ability).first()
            if existing_ability and existing_ability in self.abilities:
                self.abilities.remove(existing_ability)

    def __repr__(self):
        return '<Role {}>'.format(self.name)

    def __str__(self):
        return self.name


class Ability(db.Model):

    """
    Subclass this for your abilities
    """
    __tablename__ = 'fp_ability'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)

    def __init__(self, name):
        self.name = name.lower()

    def __repr__(self):
        return '<Ability {}>'.format(self.name)

    def __str__(self):
        return self.name

class Container(db.Model):

    """
    Subclass this for your container
    """
    __tablename__ = 'fp_container'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Container {}>'.format(self.name)

    def __str__(self):
        return self.name


class User(db.Model):

    """
    Subclass this for your user class
    """
    __tablename__ = 'fp_user'
    id = db.Column(db.Integer, primary_key=True)
    _roles = db.relationship('Role', secondary=user_role_table, backref='users')
    type = db.Column(db.String(50))
    username = db.Column(db.String(60), unique=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(100))
    # 0 = None, 1 = Allow, 2 = Deny ???
    rule = db.Column(db.Integer)
    _containers = db.relationship('Container', secondary=user_container_table, backref='users')

    roles = association_proxy('_roles', 'name', creator=_role_find_or_create)
    containers = association_proxy('_containers', 'name', creator=_container_find_or_create)

    __mapper_args__ = {
        'polymorphic_identity': 'usermixin',
        'polymorphic_on': type
    }

    def __init__(self, containers=None, roles=None, default_role='user', default_container='all'):
        # If only a string is passed for roles, convert it to a list containing
        # that string
        if roles and isinstance(roles, basestring):
            roles = [roles]

        # If a sequence is passed for roles (or if roles has been converted to
        # a sequence), fetch the corresponding database objects and make a list
        # of those.
        if roles and is_sequence(roles):
            self.roles = roles
        # Otherwise, assign the default 'user' role. Create that role if it
        # doesn't exist.
        elif default_role:
            self.roles = [default_role]


        if containers and isinstance(containers, basestring):
            containers = [containers]
        if containers and is_sequence(containers):
            self.containers = containers
        elif default_container:
            self.containers = [default_container]

    def hash_password(self, password):
        self.password = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def add_roles(self, *roles):
        self.roles.extend([role for role in roles if role not in self.roles])

    def remove_roles(self, *roles):
        self.roles = [role for role in self.roles if role not in roles]

    def add_containers(self, *containers):
        self.containers.extend([container for container in containers if container not in self.containers])

    def remove_containers(self, *containers):
        self.containers = [container for container in self.containers if container not in containers]

    def get_id(self):
        return str(self.id, 'utf-8')

    def __repr__(self):
        return '<User {}>'.format(self.id)
