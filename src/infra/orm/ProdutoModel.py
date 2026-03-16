#Peterson Wiggers
from infra import database
from sqlalchemy import Column, VARCHAR, Integer, DECIMAL, BLOB

# ORM
class ProdutoDB(database.Base):
    __tablename__ = 'tb_produto'
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    nome = Column(VARCHAR(100), nullable=False, index=True)
    descricao = Column(VARCHAR(150), nullable=False, index=True)
    valor_unitario = Column(DECIMAL(10, 2), nullable=False)
    foto = Column(BLOB, nullable=True)
    def __init__(self, id, nome, descricao, foto, valor_unitario):
        self.id = id
        self.nome = nome
        self.descricao = descricao
        self.foto = foto
        self.valor_unitario = valor_unitario