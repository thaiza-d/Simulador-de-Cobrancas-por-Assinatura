from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_db, verificar_token
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from ..models import Usuario, Assinatura, Transacao, Planos, EnumAssinatura, EnumTransacao, EnumPagamento
from ..schemas import PlanosCreate, PlanosResponse, TransacaoCreate, TransacaoResponse, AssinaturaCreate, AssinaturaResponse, simular_processamento_pagamento, PlanosUpdate, TotalCobrancasResponse
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal

router = APIRouter(prefix="/cobrancas-assinatura", tags=["cobrancas-assinatura"])

@router.post("/planos/cadastrar-planos", response_model=PlanosResponse)
async def cadastrar_planos(plano: PlanosCreate, db: Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="Apenas admins podem realizar essa ação")
    novo_plano = Planos(
        nome_plano = plano.nome_plano,
        valor_plano = plano.valor_plano
    )
    db.add(novo_plano)
    db.commit()
    db.refresh(novo_plano)
    return novo_plano

@router.put("/planos/atualizar-planos/{id_plano}", response_model=PlanosResponse)
async def atualizar_planos(id_plano: int, plano: PlanosUpdate, db: Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    if not user.admin:
            raise HTTPException(status_code=403, detail="Apenas admins podem realizar essa ação")
    verificar = db.query(Planos).filter(Planos.id == id_plano).first()
    if not verificar:
         raise HTTPException(status_code=404, detail="Plano não encontrado")
    verificar.nome_plano = plano.nome_plano
    verificar.valor_plano = plano.valor_plano
    db.commit()
    db.refresh(verificar)
    return verificar

@router.get("/planos/exibir-planos", response_model=list[PlanosResponse])
async def exibir_planos(user:Usuario=Depends(verificar_token), db: Session=Depends(get_db)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="Essa ação é somente permitida por admins.")
    return db.query(Planos).all()

@router.post("/assinatura/criar-assinatura", response_model=AssinaturaResponse)
async def criar_assinatura(assinatura: AssinaturaCreate, db: Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    usuario = db.query(Usuario).filter(Usuario.id == user.id).first()
    if not usuario:
        raise HTTPException(status_code=404,detail="Usuário não localizado")

    plano = db.query(Planos).filter(Planos.id == assinatura.plano_id).first()
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    
    verificar = db.query(Assinatura).filter(Assinatura.usuario_id == user.id, Assinatura.status_assinatura == EnumAssinatura.ATIVO).first()
    if verificar:
        raise HTTPException(status_code=409, detail="Usuário já possui uma assinatura ativa")
    nova_assinatura = Assinatura(
        usuario_id = user.id,
        plano_id = assinatura.plano_id,
        dia_cobranca = assinatura.dia_cobranca,
        status_assinatura = EnumAssinatura.ATIVO
    )
    db.add(nova_assinatura)
    db.commit()
    db.refresh(nova_assinatura)
    return nova_assinatura

@router.put("/assinatura/atualizar-assinatura", response_model=AssinaturaResponse)
async def atualizar_assinatura(assinatura: AssinaturaCreate, db: Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    assinatura_atual = db.query(Assinatura).filter(
        Assinatura.usuario_id == user.id,
        Assinatura.status_assinatura == EnumAssinatura.ATIVO,
    ).first()
    if not assinatura_atual:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada")
    
    plano = db.query(Planos).filter(Planos.id == assinatura.plano_id).first()
    if not plano:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    assinatura_atual.plano_id = assinatura.plano_id
    assinatura_atual.dia_cobranca = assinatura.dia_cobranca
    db.commit()
    db.refresh(assinatura_atual)
    return assinatura_atual

@router.get("/assinatura/exibir-assinaturas", response_model=list[AssinaturaResponse])
async def exibir_assinaturas(db:Session=Depends(get_db), user: Usuario=Depends(verificar_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="Essa ação é somente permitida por admins.")
    return db.query(Assinatura).all()

@router.put("/assinatura/cancelar-assinatura", response_model= AssinaturaResponse)
async def cancelar_assinatura(db: Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    assinatura = db.query(Assinatura).filter(Assinatura.usuario_id == user.id).first()
    if not assinatura:
        raise HTTPException(status_code=404, detail="Não foi possível localizar a sua assinatura")
    if assinatura.status_assinatura == EnumAssinatura.CANCELADO:
         raise HTTPException(status_code=409, detail="Esta assinatura já está cancelada")
    assinatura.status_assinatura = EnumAssinatura.CANCELADO
    assinatura.data_fim = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assinatura)
    return assinatura

@router.post("/transacao/registrar-pagamentos", response_model=TransacaoResponse)
async def registrar_pagamentos(transacao: TransacaoCreate, db: Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    dados = db.query(Assinatura).filter(Assinatura.id == transacao.assinatura_id, Assinatura.status_assinatura == EnumAssinatura.ATIVO).first()
    if not dados:
        raise HTTPException(status_code=404, detail="Não foi possível localizar a sua assinatura ou assinatura inativa")

    valor = dados.planos.valor_plano

    registrar = Transacao(
        assinatura_id = transacao.assinatura_id,
        valor_pagamento = valor,
        metodo_pagamento = transacao.metodo_pagamento,
        status_transacao = simular_processamento_pagamento()
    )
    db.add(registrar)
    db.commit()
    db.refresh(registrar)
    return registrar

@router.get("/transacao/exibir-transacoes", response_model=list[TransacaoResponse])
async def exibir_transacoes(db:Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="Apenas admins podem realizar essa ação")
    return db.query(Transacao).all()

# Total de cobranças no mês
@router.get("/transacao/total-cobrancas-mes", response_model=TotalCobrancasResponse)
async def total_cobrancas_mes(db:Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="Apenas admins podem realizar essa ação")

    agora = datetime.now()
    mes_atual = agora.month
    ano_atual = agora.year
    
    total = db.query(
        func.sum(Transacao.valor_pagamento)
        ).filter(
            extract("month", Transacao.data_pagamento == mes_atual),
            extract("year", Transacao.data_pagamento == ano_atual)
        ).scalar()

    return {"total_cobrancas_mes": total or Decimal("0.00")}


@router.get("/transacao/relatorio/{data_inicio}/{data_fim}")
async def relatorio(data_inicio: date, data_fim: date, db:Session=Depends(get_db), user:Usuario=Depends(verificar_token)):
    if not user.admin:
        raise HTTPException(status_code=403, detail="Apenas admins podem realizar essa ação")

    if data_inicio > data_fim:
        raise HTTPException(status_code=404, detail="A data de inicio precisa ser anterior a data fim")
    
    total_periodo = db.query(func.count(Transacao.id)).filter(
        Transacao.data_pagamento >= data_inicio,
        Transacao.data_pagamento < data_fim + timedelta(days=1) # para contar todas as movimentações até o último dia de forma integral, pois sem usar o "timedelta(days=1)" será contabilizado até a data_fim às 0:00, sem contar o que ocorreu naquelas 24h inteira.
    ).scalar()

    aprovadas_periodo = db.query(func.count(Transacao.id)).filter(
        Transacao.data_pagamento >= data_inicio,
        Transacao.data_pagamento < data_fim + timedelta(days=1),
        Transacao.status_transacao == EnumTransacao.APROVADO
    ).scalar()

    receita_aprovada_periodo = db.query(func.sum(Transacao.valor_pagamento)).filter(
        Transacao.data_pagamento >= data_inicio,
        Transacao.data_pagamento < data_fim + timedelta(days=1),
        Transacao.status_transacao == EnumTransacao.APROVADO
    ).scalar() or 0

    canceladas_periodo = db.query(func.count(Transacao.id)).filter(
        Transacao.data_pagamento >= data_inicio,
        Transacao.data_pagamento < data_fim + timedelta(days=1),
        Transacao.status_transacao == EnumTransacao.CANCELADO
        ).scalar()

    taxa_aprovacao = (aprovadas_periodo / total_periodo * 100) if total_periodo > 0 else 0

    return {
        "total_cobrancas": total_periodo,
        "aprovadas_periodo": aprovadas_periodo,
        "taxa_aprovacao": round(taxa_aprovacao, 2),
        "canceladas_periodo": canceladas_periodo,
        "receita_aprovada_periodo": receita_aprovada_periodo
    }    
