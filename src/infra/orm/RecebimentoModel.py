# Peterson Wiggers
from infra import database
from fastapi import HTTPException, status
from sqlalchemy import Column, VARCHAR, Integer, DECIMAL, DateTime
from datetime import datetime

#Tabela para armazenar os recebimentos, ou seja, os fechamentos de caixa, que podem conter uma ou mais comandas pagas naquele recebimento. O recebimento é o registro do pagamento, enquanto as comandas associadas a ele indicam quais pedidos foram pagos naquele fechamento.

# ORM
class RecebimentoDB(database.Base):
    __tablename__ = 'tb_recebimento'
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    cliente_id = Column(Integer, nullable=True, index=True) # Pode ser null se não quiserem CPF na nota
    funcionario_id = Column(Integer, nullable=False, index=True)
    subtotal_geral = Column(DECIMAL(10, 2), nullable=False)
    desconto_total = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    acrescimo_total = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    valor_final = Column(DECIMAL(10, 2), nullable=False)
    data_hora = Column(DateTime, nullable=False)

    def __init__(self, id, funcionario_id, subtotal_geral, valor_final, cliente_id=None, desconto_total=0.00, acrescimo_total=0.00, data_hora=None):
        self.id = id
        
        # Validações de integridade no momento da inicialização
        if(funcionario_id == None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O funcionário responsável pelo fechamento é obrigatório.");
            
        if(subtotal_geral == None or subtotal_geral < 0):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O subtotal geral é obrigatório e não pode ser negativo.");
            
        if(valor_final == None or valor_final < 0):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="O valor final do recebimento é obrigatório e não pode ser negativo.");
            
        self.cliente_id = cliente_id
        self.funcionario_id = funcionario_id
        self.subtotal_geral = subtotal_geral
        self.desconto_total = desconto_total if desconto_total != None else 0.00
        self.acrescimo_total = acrescimo_total if acrescimo_total != None else 0.00
        self.valor_final = valor_final
        self.data_hora = data_hora if data_hora != None else datetime.now()