"""Minimal, dependency-free password hashing.

Deliberately simple (SHA-256, no complexity rules) for this personal app: an
empty password hashes to a fixed digest, which is how the seeded demo accounts
(Zoey, Xiaoming) are left password-less. If this ever becomes a public site,
swap this for a salted KDF (bcrypt/argon2) — see CLAUDE.md."""
import hashlib


def hash_password(pw: str) -> str:
    return hashlib.sha256((pw or "").encode("utf-8")).hexdigest()


def verify_password(pw: str, stored: str) -> bool:
    return hash_password(pw) == (stored or "")


EMPTY_PASSWORD_HASH = hash_password("")
