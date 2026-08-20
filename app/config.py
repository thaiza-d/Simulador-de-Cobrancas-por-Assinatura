from dotenv import load_dotenv
import os
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM=os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES= int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

RESEND_API_KEY=os.getenv("RESEND_API_KEY")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_schema= OAuth2PasswordBearer(tokenUrl= "auth/login-auth")

def hash_senha(senha: str) -> str:
    return pwd_context.hash(senha)

def verificar_senha(senha: str, hash:str) -> bool:
    return pwd_context.verify(senha, hash)
