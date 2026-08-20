from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import date, datetime
from enum import Enum
from decimal import Decimal
import random
import re

class EnumPlano(str, Enum):
    BASICO = "basico"
    PREMIUM = "premium"

class EnumAssinatura(str, Enum):
    ATIVO = "ativo"
    CANCELADO = "cancelado"

class EnumTransacao(str, Enum):
    APROVADO = "aprovado"
    PENDENTE = "pendente"
    CANCELADO = "cancelado"

class EnumPagamento(str, Enum):
    CREDITO = "credito"
    DEBITO = "debito"
    PIX = "pix"

def simular_processamento_pagamento() -> EnumTransacao:
    return EnumTransacao.APROVADO if random.random() < 0.85 else EnumTransacao.CANCELADO


class BaseResponse(BaseModel):
    class Config():
        from_attributes = True


class UsuarioCreate(BaseModel):
    nome_usuario: str
    senha: str
    cpf: str
    email: EmailStr
    data_nascimento: date
    telefone: str
    ativo: bool = True
    admin: bool = False

#Confere se o CPF é válido e torna inválido os caracteres especiais
    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor):
        cpf = re.sub(r"\D", "", valor)  # remove tudo que não é dígito
        if len(cpf) != 11 or cpf == cpf[0] * 11:  # 11 dígitos iguais também é inválido
            raise ValueError("CPF inválido")

        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        digito1 = (soma * 10 % 11) % 10
        if digito1 != int(cpf[9]):
            raise ValueError("CPF inválido")

        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        digito2 = (soma * 10 % 11) % 10
        if digito2 != int(cpf[10]):
            raise ValueError("CPF inválido")

        return cpf

#Verifica se o telefone é válido e sem caracteres especiais.
    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, valor):
        telefone = re.sub(r"\D", "", valor)
        if not re.fullmatch(r"\d{10,11}", telefone):
            raise ValueError("Telefone deve ter 10 ou 11 dígitos (com DDD)")
        return telefone

class UsuarioUpdate(BaseModel):
    nome_usuario: Optional[str] = None
    email: Optional[EmailStr] = None
    data_nascimento: Optional[date] = None
    telefone: Optional[str] = None

class UsuarioResponse(BaseResponse):
    id: int
    nome_usuario: str
    cpf: str
    email: EmailStr
    data_nascimento: date
    telefone: str
    admin: bool
    ativo: bool

class UsuarioLogin(BaseModel):   
    cpf: str
    senha: str

class PlanosCreate(BaseModel):
    nome_plano: EnumPlano
    valor_plano: Decimal

class PlanosUpdate(BaseModel):
    nome_plano: Optional[EnumPlano] = None
    valor_plano: Optional[Decimal] = None

class PlanosResponse(BaseResponse):
    id: int
    nome_plano: EnumPlano
    valor_plano: Decimal

class AssinaturaCreate(BaseModel):
    plano_id: int
    dia_cobranca: int


class AssinaturaResponse(BaseResponse):
    id: int
    usuario_id: int
    plano_id: int
    data_inicio: date
    data_fim: Optional[date] = None
    dia_cobranca: int
    status_assinatura: EnumAssinatura

class TransacaoCreate(BaseModel):
    assinatura_id: int
    metodo_pagamento: EnumPagamento

class TransacaoResponse(BaseResponse):
    id: int
    assinatura_id: int
    status_transacao: EnumTransacao
    valor_pagamento: Decimal
    metodo_pagamento: EnumPagamento
    data_pagamento: date

class RefreshTokenResponse(BaseResponse):
    token: str
    expira_em: datetime
    ativo_token: bool

class TrocarSenha(BaseModel):
    senha_atual: str
    senha_nova: str

class TotalCobrancasResponse(BaseModel):
    total_cobrancas_mes: Decimal
