from flask_login import UserMixin


class User(UserMixin):
    """Models a user."""
    def __init__(self, username, email, password, user_id=None,
                 default_profile=""):
        """Initialize instance variables."""
        self.username = username
        self.id = user_id
        self.email = email
        self.password = password
        self.default_profile = default_profile

    def __repr__(self):
        """Return a formal representation of self."""
        return (f"User(username='{self.username}', "
                f"email='{self.email}', id='{self.id}, profiles={self.profiles})'")

    def get_id(self):
        """
        Return the unique identifier used to identify this instance.

        Use the username for identification.
        """
        return self.username

    def set_default_profile(self, profile):
        """Set the default profile for this user."""
        from app import db
        db.set_default_profile(self.username, profile)
        db.save()
        self.default_profile = profile
