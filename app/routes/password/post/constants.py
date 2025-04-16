import os

if salt := os.getenv("USER_SALT"):
    USER_SALT = salt.encode()
else:
    raise ValueError("SALT not set")
