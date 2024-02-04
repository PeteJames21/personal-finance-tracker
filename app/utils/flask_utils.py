from datetime import datetime

from flask_login import current_user
from flask import session, request


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


def get_request_args(r: request) -> dict:
    """
    Load arguments from a request URL.

    Arguments that are not found are substituted with appropriate defaults.
    """
    start_date = r.args.get('startDate')
    end_date = r.args.get('endDate')
    profile = r.args.get('selectedProfile')
    if profile:
        session['profile'] = profile
    else:
        profile = get_current_profile()

    date_now = datetime.now()
    if not start_date:
        # Set the start date to the first day of the month
        start_date = (
            datetime(
                year=date_now.year, month=date_now.month, day=1
            ).strftime("%Y-%m-%d")
        )
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")

    return {
        'start_date': start_date,
        'end_date': end_date,
        'profile': profile
    }
