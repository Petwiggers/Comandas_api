# Peterson Wiggers
from infra import database
from fastapi import HTTPException, status
from sqlalchemy import Column, Integer, ForeignKey

##Tabela para relacionar os recebimentos com as comandas pagas naquele recebimento, já que um recebimento pode pagar várias comandas e uma comanda pode ser paga por vários recebimentos (em casos de pagamentos parciais)

# ORM da Tabela Associativa
class RecebimentoComandaDB(database.Base):
    __tablename__ = 'tb_recebimento_comanda'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    recebimento_id = Column(Integer, nullable=False, index=True) # ID do fechamento do caixa
    comanda_id = Column(Integer, nullable=False, index=True)     # ID da comanda que foi paga
    
    def __init__(self, id, recebimento_id, comanda_id):
        self.id = id
        
        if(recebimento_id == None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O ID do recebimento é obrigatório.");
            
        if(comanda_id == None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O ID da comanda é obrigatório.");
            
        self.recebimento_id = recebimento_id
        self.comanda_id = comanda_id