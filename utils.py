from .decorators import import_user

def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))

def is_user_has(ability, get_user=import_user):
    from .models import Ability
    desired_ability = Ability.query.filter_by(name=ability).first()
    user_abilities = []
    current_user = get_user()
    for role in current_user._roles:
        user_abilities += role.abilities
    if desired_ability in user_abilities:
        return True
    else:
        return False