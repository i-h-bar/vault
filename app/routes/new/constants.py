import os

if salt := os.getenv("SALT"):
    SALT = salt.encode()
else:
    raise ValueError("SALT not set")
