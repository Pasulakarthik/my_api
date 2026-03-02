from passlib.context import CryptContext


pass_context = CryptContext(schemes=['argon2'],deprecated = "auto")

def hash_password(password:str) -> str:
    return pass_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pass_context.verify(plain_password , hash_password)