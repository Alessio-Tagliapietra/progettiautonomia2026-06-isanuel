try:
    from flask_login import UserMixin
except ImportError as e:
    print(f"Errore nel caricamento dei moduli in user.py: {e}")
    
    
class User(UserMixin):
    def __init__(self, email):
        self.id = email
        self.email = email
