import pytest
from app.database import Base
from app.dependencies import get_db
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine
from fastapi.testclient import TestClient
from ..main import app
from app.models import EnumPlano, Planos, Usuario
from decimal import Decimal
from datetime import date

#Cria um novo banco para testes, esse banco fica na memória e é separado do banco utilizado para produção
TESTE_DATABASE_URL = "sqlite:///./teste.db"

engine = create_engine(TESTE_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)


TestingSessionLocal = sessionmaker(autocommit=False,
                                   autoflush=False,
                                   bind=engine)


#Fazendo um novo "get_db" para executar e substituir o que está sendo rodado nos endpoints
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

#Cada teste usa os models criados, porém o sqlite não interage bem com BigInteger para autoincrement, então tive que refazer essa coluna dentro de testes. Primeiro ele apaga o que tem em memória e depois cria, já colocando a coluna sugerida dentro deste arquivo, assim colocando dentro do sqlite e depois esvaziando. Logo cada vez que roda recebe um banco sqlite limpo.

#O get_db que está nos meus endpoints é substituido pelo override_get_db, que inicia, executa e encerra a sessão 
@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def db(client):
    """Sessão ligada ao mesmo banco isolado utilizado pelo cliente de teste."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def usuario(db):
    usuario_teste = Usuario(
        nome_usuario="Usuário da assinatura",
        senha="hash-de-teste",
        cpf="12345678909",
        email="assinatura@teste.com",
        data_nascimento=date(2000, 1, 1),
        telefone="21988888888",
    )
    db.add(usuario_teste)
    db.commit()
    db.refresh(usuario_teste)
    return usuario_teste


@pytest.fixture
def plano(db):
    plano_teste = Planos(
        nome_plano=EnumPlano.BASICO,
        valor_plano=Decimal("59.90"),
    )
    db.add(plano_teste)
    db.commit()
    db.refresh(plano_teste)
    return plano_teste
