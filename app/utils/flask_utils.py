from flask_login import current_user
from flask import session


def get_current_profile():
    """Get the current profile associated with the current logged-in user."""
    # To get the profile to load:
    # 1. Use the 'profile' variable in the session, else
    # 2. Use the 'default_profile' on the `current_user object`, else
    if not current_user.is_authenticated:
        # TODO: use a more specific exception
        raise Exception('The current user is not authenticated')
    if profile := session.get('profile'):
        return profile
    elif current_user.default_profile:
        return current_user.default_profile
    else:
        return None
