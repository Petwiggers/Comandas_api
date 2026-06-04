# Peterson Wiggers
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime
from .ClienteSchema import ClienteResponse
from .FuncionarioSchema import FuncionarioResponse
from .ComandaSchema import ComandaResponse
from .ProdutoSchema import ProdutoResponse


# ==========================================
# SCHEMAS DO DASHBOARD E PREVIEW
# ==========================================

class RecebimentoDashboardItem(BaseModel):
    """Estrutura simplificada para listar no painel inicial do caixa"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    comanda: str
    status: int
    cliente:  Optional[str] = None
    total: float
    quantidade_produtos: int
    data_hora: datetime


# ==========================================
# SCHEMAS DE ENVIO E RESPOSTA (POST)
# ==========================================

class RecebimentoCompletoRequest(BaseModel):
    """Payload enviado pelo Frontend para fechar uma ou mais comandas"""
    comandas_ids: List[int]
    cliente_id: Optional[int] = None
    funcionario_id: int
    desconto_valor: Optional[float] = None
    acrescimo_valor: Optional[float] = None

class RecebimentoCompletoResponse(BaseModel):
    """Retorno após a confirmação do pagamento no banco de dados"""
    model_config = ConfigDict(from_attributes=True)
    sucesso: bool
    mensagem: str
    recebimento_id: int
    comandas_pagas: List[ComandaResponse]
    subtotal_geral: float
    desconto_total: float
    acrescimo_total: float
    valor_final: float
    cliente: Optional[ClienteResponse] = None
    funcionario: FuncionarioResponse
    data_hora: datetime


# ==========================================
# SCHEMA DE COMPROVANTE (Impressão)
# ==========================================

class ComprovanteRecebimento(BaseModel):
    """Dados completos e formatados para gerar a impressão do cupom"""
    model_config = ConfigDict(from_attributes=True)
    cabecalho: dict  # Dados do restaurante (Razão Social, CNPJ, etc.)
    cliente: Optional[ClienteResponse] = None
    funcionario: FuncionarioResponse
    comandas: List[ComandaResponse]
    resumo_valores: dict  # Detalhamento de formas de pagamento e troco
    recebimento: dict  # Informações gerais da transação
    rodape: dict  # Mensagens customizadas de agradecimento
    data_emissao: datetime


class RecebimentoItemDetalhe(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    produto_id: int
    produto: str
    quantidade: int
    valor_unitario: float
    total_item: float


class RecebimentoComandaDetalheResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    comanda: str
    itens: List[RecebimentoItemDetalhe]
    subtotal: float
    quantidade_total: int


class RecebimentoComandasDetalheResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    comandas: List[RecebimentoComandaDetalheResponse]
    total_geral: float
    quantidade_total: int