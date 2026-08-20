from .database import SessionLocal
from sqlalchemy.orm import Session
from .models import Usuario, Assinatura, EnumTransacao, EnumPagamento, Transacao
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from .config import SECRET_KEY, ALGORITHM, oauth2_schema
from datetime import datetime, timezone
from .extensions import scheduler

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verificar_token(token:str = Depends(oauth2_schema), db: Session=Depends(get_db)):
    try:
        dic_info= jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        id_usuario = int(dic_info.get("sub"))

    except JWTError:
        raise HTTPException(status_code=401, detail="Acesso Negado: Verifique a validade do token")
    usuario = db.query(Usuario).filter(Usuario.id == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Acesso inválido")
    return usuario


def gerar_cobrancas_mensais():
    db = SessionLocal()
    # Busca todas assinaturas ativas
    assinaturas = db.query(Assinatura).filter(Assinatura.status_assinatura == True).all()
    for assinatura in assinaturas:
        valor = assinatura.planos.valor_plano
        transacao = Transacao(
            assinatura_id=assinatura.id,
            valor_pagamento=valor,
            metodo_pagamento=EnumPagamento.CARTAO,  # ou outro padrão
            status_transacao=EnumTransacao.PENDENTE,
            data_pagamento=datetime.now(timezone.utc)
        )
        db.add(transacao)
    db.commit()
    db.close()
scheduler.add_job(gerar_cobrancas_mensais, "interval", weeks=4)

