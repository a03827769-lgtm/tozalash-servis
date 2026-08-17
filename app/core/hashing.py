from passlib.context import CryptContext

# Task 39: Use Argon2id instead of bcrypt for stronger security against GPU-based cracking
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=2,  # OWASP recommendation
    argon2__memory_cost=65536,
    argon2__parallelism=2,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
