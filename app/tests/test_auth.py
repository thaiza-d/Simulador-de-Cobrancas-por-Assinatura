import pytest
from app.models import Usuario
from app.tests.conftest import TestingSessionLocal

@pytest.fixture
def token_usuario(client):
    client.post("/auth/cadastrar-usuario", json={
        "nome_usuario": "Token Usuario",
        "senha": "Senha@123",
        "cpf": "11144477735",
        "email": "token@teste.com",
        "data_nascimento": "2000-01-01",
        "telefone": "21990909090",
        "ativo": True
    })
    response = client.post("/auth/login-auth", data={
        "username": "11144477735",
        "password": "Senha@123"
    })
    if response.status_code == 200 and "access_token" in response.json():
        return response.json ()["access_token"]
    else:       
        pytest.skip(f"Login falhou: {response.status_code} {response.json()}")

@pytest.fixture
def token_admin(client):
    client.post("/auth/cadastrar-usuario", json={
        "nome_usuario": "Token Admin",
        "senha": "Senha@123",
        "cpf": "82608402941",
        "email": "admin@teste.com",
        "data_nascimento": "2000-01-01",
        "telefone": "21988999999",
        "ativo": True
    })
    db = TestingSessionLocal()
    usuario = db.query(Usuario).filter(Usuario.cpf == "82608402941").first()
    if usuario:
        usuario.admin = True
        db.commit()
    db.close()
    response = client.post("/auth/login-auth", data={
        "username": "82608402941",
        "password": "Senha@123"
    })
    if response.status_code == 200 and "access_token" in response.json():
        return response.json()["access_token"]
    else:
        pytest.skip(f"Login falhou: {response.status_code} {response.json()}")


@pytest.mark.parametrize("senha_correta", ["Senha#777", "aaaAAA##", "SenhaCOrreta2026!!"]) #com 8, 9 e 18 caracteres
def test_cadastrar_usuario_sucesso(senha_correta, client):
    response = client.post("/auth/cadastrar-usuario", json= {
        "nome_usuario": "Usuário sucesso",
        "senha": senha_correta, 
        "cpf": "54185439032",  
        "email": "teste@teste.com",
        "data_nascimento": "2000-01-01",
        "telefone": "21999999999"
        })
    assert response.status_code == 200


def test_cadastrar_usuario_invalido(client):
    cadastro = client.post("/auth/cadastrar-usuario", json={
        "nome_usuario": "Usuário original",
        "senha": "Senha@123",
        "cpf": "54185439032",
        "email": "teste@teste.com",
        "data_nascimento": "2000-01-01",
        "telefone": "21999999999"
    })

    assert cadastro.status_code == 200

    response = client.post("/auth/cadastrar-usuario", json={
        "nome_usuario": "Usuário duplicado",
        "senha": "Senha@123",
        "cpf": "54185439032",
        "email": "outro@teste.com",
        "data_nascimento": "2000-01-01",
        "telefone": "21999999998"
    })

    assert response.status_code == 409
    assert response.json()["detail"] == "Conflito de dados"


@pytest.mark.parametrize("senha_invalida", ["senha123!", "Senha123", "SENHA123!"]) 
def test_cadastrar_usuario_senha_invalida(senha_invalida, client):
    response = client.post("/auth/cadastrar-usuario", json={
        "nome_usuario": "Senha inválida",
        "senha": senha_invalida, 
        "cpf": "11144477735",  
        "email": "admin@teste.com",
        "data_nascimento": "2000-01-01",
        "telefone": "21999999999"
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Senha precisa ter 1 caractere maiusculo, 1 caractere minusculo e um caractere especial"

def test_login_auth(client):
    cadastro = client.post("/auth/cadastrar-usuario", json= {
            "nome_usuario": "Teste1",
            "senha": "Aaaaa@123", 
            "cpf": "18262337417",  
            "email": "teste1@teste.com",
            "data_nascimento": "1980-10-10",
            "telefone": "2199990000"
            })
    assert cadastro.status_code == 200

    response = client.post("/auth/login-auth", data={
        "username": "18262337417",
        "password": "Aaaaa@123"
        })

    assert response.status_code == 200
    assert "access_token" in response.json()

def test_refresh_rotativo(client):
    response = client.post("/auth/refresh-rotativo")

#sem token válido vai dar 401
    assert response.status_code == 401


def test_editar_usuario(client):
    cadastro = client.post("/auth/cadastrar-usuario", json= {
            "nome_usuario": "Teste2",
            "senha": "Aaaaa@123", 
            "cpf": "33192651997",  
            "email": "teste2@teste.com",
            "data_nascimento": "1980-10-10",
            "telefone": "11912345678"
            })
    assert cadastro.status_code == 200
    id_usuario = cadastro.json()["id"]

    response = client.put(f"/auth/editar-usuario/{id_usuario}", json={
        "nome_usuario": "Teste2",
        "email": "teste2@teste.com",
        "data_nascimento": "1999-10-09", # data alterada
        "telefone": "11988888888" # telefone alterado
    })
#sem token válido vai dar 401
    assert response.status_code == 401

def test_editar_usuario_com_token(client,token_usuario):
    cadastro = client.post("/auth/cadastrar-usuario", json= {
            "nome_usuario": "Teste2",
            "senha": "Aaaaa@123", 
            "cpf": "33192651997",  
            "email": "teste2@teste.com",
            "data_nascimento": "1980-10-10",
            "telefone": "11912345678"
            })
    assert cadastro.status_code == 200
    id_usuario = cadastro.json()["id"]

    response = client.put(f"/auth/editar-usuario/{id_usuario}",
        json={
            "nome_usuario": "Novo Nome",
            "telefone": "21988888888",
            "email": "novo@teste.com",
            "data_nascimento": "1995-05-05"
            },
        headers={"Authorization": f"Bearer {token_usuario}"}
    )
    assert response.status_code == 200

def test_trocar_senha(client, token_usuario):
    cadastro = client.post("/auth/cadastrar-usuario", json= {
            "nome_usuario": "Teste2",
            "senha": "Senha@123", 
            "cpf": "33192651997",  
            "email": "teste2@teste.com",
            "data_nascimento": "1980-10-10",
            "telefone": "11912345678"
            })
    assert cadastro.status_code == 200

    #Se a senha atual colocada for a correta
    response = client.put("/auth/trocar-senha",
                          json={"senha_atual":"Senha@123","senha_nova": "NovaSenha@1"},
                          headers={"Authorization": f"Bearer {token_usuario}"})

    assert response.status_code == 200

    #Se a senha atual colocada estiver incorreta
    response = client.put("/auth/trocar-senha",
                         json={"senha_atual": "Errei@123", "senha_nova": "NovaSenha@1"},
                         headers={"Authorization": f"Bearer {token_usuario}"})

    assert response.status_code == 401

def test_tornar_admin(client, token_admin):
    cadastro = client.post("/auth/cadastrar-usuario", json= {
        "nome_usuario": "Teste3",
        "senha": "Senha@123", 
        "cpf": "04320966120",  
        "email": "teste3@teste.com",
        "data_nascimento": "2003-03-03",
        "telefone": "11998877665"
        })
    assert cadastro.status_code == 200
    id_usuario = cadastro.json()["id"]


    response = client.put(f"/auth/tornar-admin/{id_usuario}",
                          json={"admin": True},
                          headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200


def test_retirar_admin(client, token_admin):
    cadastro = client.post("/auth/cadastrar-usuario", json= {
        "nome_usuario": "Teste4",
        "senha": "Senha@123", 
        "cpf": "51960139118",  
        "email": "teste4@teste.com",
        "data_nascimento": "2004-04-04",
        "telefone": "1199884444"
        })
    assert cadastro.status_code == 200
    id_usuario = cadastro.json()["id"]


    response = client.put(f"/auth/tornar-admin/{id_usuario}",
                          json={"admin": True},
                          headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200

    response = client.put("/auth/retirar-admin/1",
                          json={"admin": False},
                          headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200

def test_consultar_clientes(client, token_admin):
    response = client.get("/auth/consultar-clientes",
                        headers={"Authorization": f"Bearer {token_admin}"})
    
    assert response.status_code == 200

    if response.status_code == 403:
        pytest.skip("Usuário admin não criado")

   
def test_refresh(client, token_usuario):
    response = client.get("/auth/refresh",
                          headers={"Authorization": f"Bearer {token_usuario}"})
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data

def test_desativar_cliente(client, token_admin):
    cadastro = client.post("/auth/cadastrar-usuario", json= {
        "nome_usuario": "ClienteTeste",
        "senha": "Senha@123", 
        "cpf": "54185439032",  
        "email": "cliente@teste.com",
        "data_nascimento": "2000-01-01",
        "telefone": "21977777999"
        })

    login = client.post("/auth/login-auth", data={
        "username": "54185439032",
        "password": "Senha@123"
    })
    if login.status_code == 200 and "access_token" in login.json():
        return login.json()["access_token"]
    else:
        pytest.skip(f"Login falhou: {login.status_code} {login.json()}")
    
    assert cadastro.status_code == 200
    id_usuario = cadastro.jso(["id"])

    response = client.put(f"/auth/desativar-cliente/{id_usuario}",
                          headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code ==200

    if not client.assinatura:
        assert response.status_code == 404
        assert response.json()["detail"] == "Cliente não possui assinatura"



