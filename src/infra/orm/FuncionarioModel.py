#Peterson Wiggers
from infra import database
from sqlalchemy import Column, VARCHAR, CHAR, Integer
from fastapi import HTTPException, status

# ORM
class FuncionarioDB(database.Base):
    __tablename__ = 'tb_funcionario'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome = Column(VARCHAR(100), nullable=False)
    matricula = Column(CHAR(10), nullable=False)
    cpf = Column(CHAR(11), unique=True, nullable=False, index=True)
    telefone = Column(CHAR(11), nullable=False)
    grupo = Column(Integer, nullable=False)
    senha = Column(VARCHAR(200), nullable=False)
    def __init__(self, id, nome, matricula, cpf, telefone, grupo, senha):
        self.id = id
        if(nome == None or nome.strip() == ""):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O nome do funcionário é obrigatório.");
        if(matricula == None or matricula.strip() == ""):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A matrícula do funcionário é obrigatória.");
        if(cpf == None or cpf.strip() == ""):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O CPF do funcionário é obrigatório.");
        if(telefone == None or telefone.strip() == ""):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O telefone do funcionário é obrigatório.");
        if(grupo == None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O grupo do funcionário é obrigatório.");
        if(grupo != 1 and grupo != 2 and grupo != 3):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O grupo do funcionário deve ser 1, 2 ou 3.");
        self.nome = nome
        self.matricula = matricula
        self.cpf = cpf
        self.telefone = telefone
        self.grupo = grupo
        self.senha = senha