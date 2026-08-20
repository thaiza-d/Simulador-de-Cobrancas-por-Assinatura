from .database import Base
from sqlalchemy import Column, BigInteger, String, Date, Enum, Boolean, ForeignKey, CHAR, Integer, DECIMAL, DateTime
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.orm import relationship
import enum

class EnumPlano(str, enum.Enum):
    BASICO = "basico"
    PREMIUM = "premium"

class EnumAssinatura(str, enum.Enum):
    ATIVO = "ativo"
    CANCELADO = "cancelado"

class EnumTransacao(str, enum.Enum):
    APROVADO = "aprovado"
    PENDENTE = "pendente"
    CANCELADO = "cancelado"

class EnumPagamento(str, enum.Enum):
    CREDITO = "credito"
    DEBITO = "debito"
    PIX = "pix"


class Usuario(Base):
    __tablename__ = "usuario"
    id= Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome_usuario = Column(String(150), nullable=False)
    senha= Column(String(225), nullable=False)
    cpf = Column(CHAR(11), nullable=False, unique=True)
    email = Column(String(150), nullable=False, unique=True)
    data_nascimento = Column(Date, nullable=False)
    telefone = Column(String(16), nullable=False, unique=True)
    admin = Column(Boolean, default=False, nullable=False)
    ativo = Column(Boolean,default=True, nullable=False)

    assinatura = relationship("Assinatura", back_populates="usuario")

class Planos(Base):
    __tablename__= "planos"
    id= Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome_plano = Column(Enum(EnumPlano), nullable=False)
    valor_plano = Column(DECIMAL(10,2), nullable=False)

    assinatura = relationship("Assinatura", back_populates="planos")

class Assinatura(Base):
    __tablename__ = "assinatura"
    id= Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id= Column(ForeignKey("usuario.id"), nullable=False)
    plano_id= Column(ForeignKey("planos.id"), nullable=False)
    data_inicio= Column(Date, default=date.today, nullable=False)
    data_fim= Column(Date, default=date.today, nullable=True)
    dia_cobranca = Column(Integer, nullable= False)
    status_assinatura= Column(Enum(EnumAssinatura), nullable=False)

    planos= relationship("Planos", back_populates="assinatura")
    usuario= relationship("Usuario", back_populates="assinatura")
    transacao= relationship("Transacao", back_populates="assinatura")

class Transacao(Base):
    __tablename__ = "transacao"
    id= Column(Integer, primary_key=True, index=True, autoincrement=True)
    assinatura_id= Column(ForeignKey("assinatura.id"), nullable=False)
    status_transacao= Column(Enum(EnumTransacao), default= EnumTransacao.PENDENTE, nullable=False)
    valor_pagamento= Column(DECIMAL(10,2), nullable=False)
    metodo_pagamento= Column(Enum(EnumPagamento), nullable=False)
    data_pagamento= Column(Date, default=date.today(), nullable=False)

    assinatura = relationship("Assinatura", back_populates="transacao")

class RefreshToken(Base):
    __tablename__ = "refresh"
    id= Column(Integer, primary_key=True, index=True,autoincrement=True)
    usuario_id= Column(ForeignKey("usuario.id"), nullable=False, index=True)
    token = Column(String(225), unique=True, index=True)
    expira_em = Column(DateTime, default=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    ativo_token= Column(Boolean, default=True)

class TentativaLogin(Base):
    __tablename__ = "tentativas_login"
    id= Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id= Column(Integer, index=True)
    tentativas = Column(Integer, default=0)
    bloqueado_ate = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)

