from .models import Usuario
from .config import pwd_context
from .database import SessionLocal
from datetime import date
import os
from dotenv import load_dotenv

load_dotenv()


def criar_admin():
    db = SessionLocal()
    admin_existente = db.query(Usuario).filter(Usuario.admin == True).first()
    if admin_existente:
        print("Usuário já existente!")
        return

    admin = Usuario(
        nome_usuario="Admin",
        senha=pwd_context.hash(os.getenv("ADMIN_SENHA")),
        cpf=os.getenv("ADMIN_CPF"),
        email=os.getenv("ADMIN_EMAIL"),
        data_nascimento=date.fromisoformat(os.getenv("ADMIN_DATA_NASCIMENTO")),
        telefone=os.getenv("ADMIN_TELEFONE"),
        ativo=True,
        admin=True
        )


    db.add(admin)
    db.commit()
    db.close()

if __name__ == "__main__":
    criar_admin()