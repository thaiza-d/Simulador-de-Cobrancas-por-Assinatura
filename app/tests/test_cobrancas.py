from .test_auth import token_admin, token_usuario
import pytest
from ..models import EnumAssinatura, Assinatura

# CADASTRAR PLANO
def test_cadastrar_planos(client,token_admin):
    response = client.post("/cobrancas-assinatura/planos/cadastrar-planos",
                           json={"nome_plano": "basico", "valor_plano": "25.90"},
                           headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200
    assert response.json()["nome_plano"] == "basico"
    assert response.json()["valor_plano"] == "25.90" # está entre aspas, pois o decimal no Pydantic se torna string no JSON


# ATUALIZAR PLANO
@pytest.mark.parametrize("id_plano", [5,10,50])
def test_atualizar_planos_invalido(id_plano, client, token_admin):
    response = client.put(f"/cobrancas-assinatura/planos/atualizar-planos/{id_plano}",
                               json={"nome_plano": "basico", "valor_plano": 29.90},
                               headers={"Authorization": f"Bearer {token_admin}"})
        
    assert response.status_code == 404
    assert response.json()["detail"] == "Plano não encontrado"


def test_atualizar_planos_sucesso(client, token_admin):
    cadastro = client.post(
        "/cobrancas-assinatura/planos/cadastrar-planos",
        json={
            "nome_plano": "premium",
            "valor_plano": "60.90"
        },
        headers={"Authorization": f"Bearer {token_admin}"}
    )

    assert cadastro.status_code == 200

    id_plano = cadastro.json()["id"]

    response = client.put(
        f"/cobrancas-assinatura/planos/atualizar-planos/{id_plano}",
        json={
            "nome_plano": "basico",
            "valor_plano": 59.90
        },
        headers={"Authorization": f"Bearer {token_admin}"}
    )

    assert response.status_code == 200
    assert response.json()["nome_plano"] == "basico"


# EXIBIR PLANOS
def test_exibir_planos(client,token_admin):
    response = client.get("/cobrancas-assinatura/planos/exibir-planos",
                          headers={"Authorization":f"Bearer {token_admin}"})

    assert response.status_code == 200


# CRIAR ASSINATURA
@pytest.mark.parametrize("id_plano", [900, 100])
def test_criar_assinatura_erro(id_plano, client, token_usuario):
    response = client.post("/cobrancas-assinatura/assinatura/criar-assinatura",
                        json={
                            "plano_id": id_plano,
                            "dia_cobranca": 5
                            },
                        headers={"Authorization": f"Bearer {token_usuario}"})
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Plano não encontrado"


def test_criar_assinatura(client, token_usuario, token_admin):
    response = client.post("/cobrancas-assinatura/planos/cadastrar-planos",
                        json={"nome_plano": "basico", "valor_plano": "25.90"},
                        headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200
    assert response.json()["nome_plano"] == "basico"
    assert response.json()["valor_plano"] == "25.90"
    id_plano = response.json()["id"]

    cadastro = client.post("/cobrancas-assinatura/assinatura/criar-assinatura",
                           json={"plano_id": id_plano, "dia_cobranca": 7},
                           headers={"Authorization": f"Bearer {token_usuario}"})

    assert cadastro.status_code == 200
    assert cadastro.json()["plano_id"] == id_plano
    assert cadastro.json()["dia_cobranca"] == 7 


# ATUALIZAR ASSINATURA
def test_atualizar_assinatura(client, token_usuario, token_admin):
    cadastro = client.post(
        "/cobrancas-assinatura/planos/cadastrar-planos",
        json={
            "nome_plano": "premium",
            "valor_plano": "60.90"
        },
        headers={"Authorization": f"Bearer {token_admin}"}
    )

    assert cadastro.status_code == 200

    id_plano = cadastro.json()["id"]

    criar = client.post(
        "/cobrancas-assinatura/assinatura/criar-assinatura",
        json={
            "plano_id": id_plano,
            "dia_cobranca": 3
        },
        headers={"Authorization": f"Bearer {token_usuario}"}
    )

    assert criar.status_code == 200

    response = client.put(
        "/cobrancas-assinatura/assinatura/atualizar-assinatura",
        json={
            "plano_id": id_plano,
            "dia_cobranca": 10
        },
        headers={"Authorization": f"Bearer {token_usuario}"}
    )

    assert response.status_code == 200


# EXIBIR ASSINATURAS
def test_exibir_assinaturas(client, token_admin):
    response = client.get(
        "/cobrancas-assinatura/assinatura/exibir-assinaturas",
        headers={"Authorization": f"Bearer {token_admin}"}
    )

    assert response.status_code == 200


# CANCELAR ASSINATURA
def test_cancelar_assinatura(client, token_usuario, token_admin):
    plano = client.post(
        "/cobrancas-assinatura/planos/cadastrar-planos",
        json={"nome_plano": "basico", "valor_plano": "25.90"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert plano.status_code == 200

    criar = client.post(
        "/cobrancas-assinatura/assinatura/criar-assinatura",
        json={
            "plano_id": plano.json()["id"],
            "dia_cobranca": 10
        },
        headers={"Authorization": f"Bearer {token_usuario}"}
    )

    assert criar.status_code == 200


    response = client.put(
        f"/cobrancas-assinatura/assinatura/cancelar-assinatura",
        headers={"Authorization": f"Bearer {token_usuario}"}
    )

    assert response.status_code == 200


def test_cancelar_assinatura_ja_cancelada(client, token_usuario, token_admin):
    plano = client.post(
        "/cobrancas-assinatura/planos/cadastrar-planos",
        json={"nome_plano": "basico", "valor_plano": "25.90"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    criar = client.post(
        "/cobrancas-assinatura/assinatura/criar-assinatura",
        json={"plano_id": plano.json()["id"], "dia_cobranca": 10},
        headers={"Authorization": f"Bearer {token_usuario}"},
    )
    assert criar.status_code == 200

    response1 = client.put("/cobrancas-assinatura/assinatura/cancelar-assinatura",
                          json={"status_assinatura": "cancelado"},
                          headers={"Authorization": f"Bearer {token_usuario}"})

    assert response1.status_code == 200

    response2 = client.put("/cobrancas-assinatura/assinatura/cancelar-assinatura",
                              json={"status_assinatura": "cancelado"},
                              headers={"Authorization": f"Bearer {token_usuario}"})
    
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Esta assinatura já está cancelada"


# REGISTRAR PAGAMENTO
@pytest.mark.parametrize("id_assinatura", [999, 1000])
def test_registrar_pagamento_assinatura_invalida(client, token_usuario, id_assinatura):
    response = client.post(
        "/cobrancas-assinatura/transacao/registrar-pagamentos",
        json={
            "assinatura_id": id_assinatura,
            "valor_pagamento": 59.90,
            "metodo_pagamento": "credito",
            "status_transacao": "aprovado"
        },
        headers={"Authorization": f"Bearer {token_usuario}"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Não foi possível localizar a sua assinatura ou assinatura inativa"
    )

@pytest.fixture
def assinatura_ativa(db, usuario, plano):
    assinatura = Assinatura(
        usuario_id=usuario.id,
        plano_id=plano.id,
        dia_cobranca=5,
        status_assinatura=EnumAssinatura.ATIVO
    )

    db.add(assinatura)
    db.commit()
    db.refresh(assinatura)

    return assinatura

def test_registrar_pagamento(
    client,
    token_usuario,
    assinatura_ativa
):
    response = client.post(
        "/cobrancas-assinatura/transacao/registrar-pagamentos",
        json={
            "assinatura_id": assinatura_ativa.id,
            "valor_pagamento": "59.90",
            "metodo_pagamento": "credito",
            "status_transacao": "aprovado"
        },
        headers={
            "Authorization": f"Bearer {token_usuario}"
        }
    )

    assert response.status_code == 200


# EXIBIR TRANSAÇÕES
def test_exibir_transacoes(client, token_admin):
    response = client.get("/cobrancas-assinatura/transacao/exibir-transacoes",
                         headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200


# EXIBIR TOTAL DE COBRANÇAS POR MÊS
def test_total_cobrancas_mes(client,token_admin):
    response = client.get("/cobrancas-assinatura/transacao/total-cobrancas-mes",
                         headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200


# EXIBIR RELATÓRIOS DE ACORDO COM O PERIODO QUE DESEJAR
def test_total_relatorio(client,token_admin):
    response = client.get("/cobrancas-assinatura/transacao/relatorio/2026-01-01/2026-02-02",
                         headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200
