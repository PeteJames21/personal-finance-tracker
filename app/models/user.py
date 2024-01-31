from flask_login import UserMixin


class User(UserMixin):
    """Models a user."""
    def __init__(self, username, email, password, user_id=None):
        """Initialize instance variables."""
        self.username = username
        self.id = user_id
        self.email = email
        self.password = password
        

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
