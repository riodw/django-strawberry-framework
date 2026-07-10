"""Pytest-only settings layered over the shipped fakeshop configuration."""

from config.settings import *  # noqa: F403

# Password strength is validated separately from hashing. A fast hasher keeps
# repeated create_users()/login acceptance setup from spending time on PBKDF2.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
