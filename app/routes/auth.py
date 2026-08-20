from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from ..dependencies import get_db, verificar_token
from sqlalchemy.orm import Session
from ..models import Usuario, RefreshToken, TentativaLogin, Assinatura, EnumAssinatura
from ..schemas import UsuarioLogin, UsuarioResponse, UsuarioCreate, RefreshTokenResponse, UsuarioUpdate, TrocarSenha
from jose import JWTError, jwt
from datetime import timedelta, timezone, datetime
from ..config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, pwd_context
from ..extensions import limiter
import secrets
from .utils import enviar_email_alerta
from fastapi.security import OAuth2PasswordRequestForm
import re

auth_router = APIRouter(prefix="/auth", tags=["auth"])


def criar_token(id_usuario, duracao_token=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    data_expiracao = datetime.now(timezone.utc) + duracao_token
    dict_info = {"sub": str(id_usuario), "exp": data_expiracao}
    jwt_codificado=jwt.encode(dict_info, SECRET_KEY, algorithm=ALGORITHM)
    return jwt_codificado


@auth_router.post("/cadastrar-usuario")
async def cadastrar_usuario(user: UsuarioCreate, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.cpf == user.cpf).first()
    if usuario:
        raise HTTPException(status_code=409, detail="Conflito de dados")

    if len(user.senha) < 8:
        raise HTTPException(status_code=404,detail="Senha precisa ser maior ou igual a 8 caracteres")
        
    if not (re.search(r"[A-Z]", user.senha) and
        re.search(r"[a-z]", user.senha) and
        re.search(r"[^a-zA-Z0-9]", user.senha)):
        raise HTTPException(status_code=404, detail="Senha precisa ter 1 caractere maiusculo, 1 caractere minusculo e um caractere especial")
    
    senha_criptografada = pwd_context.hash(user.senha)
    novo_usuario = Usuario(
        nome_usuario = user.nome_usuario,
        senha = senha_criptografada,
        cpf = user.cpf,
        email = user.email,
        data_nascimento =user.data_nascimento,
        telefone = user.telefone
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario

@auth_router.post("/login-auth")
# @limiter.limit("5/minute") #Limita por IP
async def login(request: Request, background_tasks: BackgroundTasks, formulario: OAuth2PasswordRequestForm=Depends(), db: Session=Depends(get_db)):
    dados_login = UsuarioLogin(
        cpf = formulario.username,
        senha = formulario.password
    )
#Busca o usuário através do CPF
    usuario_encontrado = db.query(Usuario).filter(Usuario.cpf == dados_login.cpf).first()
    if not usuario_encontrado:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou senha inválida")
    
    tentativa = db.query(TentativaLogin).filter(TentativaLogin.usuario_id == usuario_encontrado.id).first()

#Verifica caso o usuário já esteja bloqueado, se sim, não dá prosseguimento
    if tentativa and tentativa.bloqueado_ate:
        background_tasks.add_task(enviar_email_alerta, usuario_encontrado.email)
        raise HTTPException(status_code=403, detail="Conta bloqueada")

# O usuário possui conta ativa e verifica se a senha está correta, caso não, irá contabilizar as tentativas. Errando 5 vezes, ficará bloqueado temporariamente por 30 minutos para tentar novamente. Nesse período acontecerá um envio para o email do usuário, sinalizando que estão tentando entrar na conta dele. Caso seja o próprio, que ignore a mensagem, caso não, que altere a senha imediatamente.
    if not pwd_context.verify(dados_login.senha, usuario_encontrado.senha):
        if not tentativa:
            tentativa = TentativaLogin(usuario_id=usuario_encontrado.id, tentativas = 1)
            db.add(tentativa)
        else:
            tentativa.tentativas += 1
            if tentativa.tentativas >= 5:
                tentativa.bloqueado_ate = (datetime.now(timezone.utc) + timedelta(minutes=30))

        db.commit()
        raise HTTPException(status_code=401, detail="Senha inválida")

#Senha correta, o usuário entra na sua conta e as tentativas retornam a zero.
    if tentativa:
        tentativa.tentativas = 0
        tentativa.bloqueado_ate = None
        db.commit()

    access_token = criar_token(usuario_encontrado.id)
    refresh_token = criar_token(usuario_encontrado.id, duracao_token=timedelta(days=7))
    return {"access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer"}

@auth_router.post("/refresh-rotativo", response_model=RefreshTokenResponse)
async def refresh_rotativo(user= Depends(verificar_token), db: Session=Depends(get_db)):
    db.query(RefreshToken).filter(RefreshToken.usuario_id==user.id, RefreshToken.ativo_token == True).update({"ativo_token": False})

    novo_token = secrets.token_urlsafe(32)
    refresh = RefreshToken(
        usuario_id=user.id,
        token=novo_token,
        expira_em=datetime.now(timezone.utc) + timedelta(days=7), ativo=True
    )
    db.add(refresh)
    db.commit()
    db.refresh(refresh)

    access_token = criar_token(user.id)

    return {
        "token": refresh.token,
        "expira_em": refresh.expira_em,
        "ativo": refresh.ativo,
        "access_token": access_token,
        "token_type": "Bearer"
    }

@auth_router.put("/editar-usuario/{id}", response_model=UsuarioResponse)
async def editar_usuario(id:int, dados: UsuarioUpdate, db: Session=Depends(get_db), user: Usuario=Depends(verificar_token)):
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if dados.nome_usuario is not None:
        usuario.nome_usuario = dados.nome_usuario

    if dados.email is not None:
        usuario.email = dados.email

    if dados.data_nascimento is not None:
        usuario.data_nascimento =dados.data_nascimento

    if dados.telefone is not None:
        usuario.telefone = dados.telefone

    db.commit()
    return usuario

@auth_router.put("/trocar-senha")
async def trocar_senha(dados: TrocarSenha, user= Depends(verificar_token), db: Session=Depends(get_db)):
    if not pwd_context.verify(dados.senha_atual, user.senha):
        raise HTTPException(status_code=401, detail="Senha atual incorreta")
    user.senha = pwd_context.hash(dados.senha_nova)
    db.commit()
    return {"mensagem": "Senha alterada com sucesso!"}

@auth_router.put("/tornar-admin/{id}")
async def tornar_admin(id:int, db: Session= Depends(get_db), user: Usuario = Depends(verificar_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="Apenas admins podem realizar essa ação")
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario.admin = True
    db.commit()
    return {"mensagem": f"Admin de id {usuario.id} e de nome: {usuario.nome_usuario} criado com sucesso!"}

@auth_router.put("/retirar-admin/{id}")
async def retirar_admin(id:int, db: Session= Depends(get_db), user: Usuario = Depends(verificar_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="Apenas admins podem realizar essa ação")
    usuario = db.query(Usuario).filter(Usuario.id == id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario.admin = False
    db.commit()
    return {"mensagem": f"Admin de id: {usuario.id} e nome: {usuario.nome_usuario} retirado com sucesso!"}    

@auth_router.put("/desativar-cliente/{id}")
async def desativar_cliente(id:int, db: Session=Depends(get_db), user=Depends(verificar_token)):
#Função exclusiva do admin
    if not user.admin:
        raise HTTPException(status_code=403, detail="Apenas admins podem realizar essa ação")
    
#Procura o id do usuário através do id informado na url
    verificar = db.query(Usuario).filter(Usuario.id==id).first()
    if not verificar:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

#Procura a assinatura do usuário
    assinatura = db.query(Assinatura).filter(Assinatura.usuario_id==verificar.id).first()
    if not assinatura:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")

#Se estiver ativa irá cancelar, dar a data fim à assinatura e desativar o usuário
    if assinatura.status_assinatura == EnumAssinatura.ATIVO:
        verificar.ativo = False # Deixo o cliente desativado
        assinatura.status_assinatura = EnumAssinatura.CANCELADO # O status de assinatura será cancelado
        assinatura.data_fim = datetime.now(timezone.utc) # A data fim será assim que realizar a operação

#Caso já esteja cancelada a assinatura, somente irá desativar o usuário
    else:
        verificar.ativo = False
    db.commit()
    return {"mensagem": f"O usuário {verificar.nome_usuario} de id {verificar.id} foi desativado com sucesso"}

@auth_router.get("/consultar-clientes", response_model=list[UsuarioResponse])
async def consultar_clientes(user: Usuario= Depends(verificar_token), db: Session= Depends(get_db)):
    usuario = db.query(Usuario).all()
    if not user.admin:
        raise HTTPException(status_code=403, detail="Usuário não autorizado")
    return usuario


@auth_router.get("/refresh")
async def user_refresh_token(usuario= Depends(verificar_token)):
    access_token = criar_token(usuario.id)
    return{
        "access_token":access_token, 
        "token_type": "Bearer"
    }
