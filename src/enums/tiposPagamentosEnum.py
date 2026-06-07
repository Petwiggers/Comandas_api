from enum import IntEnum

class TiposPagamentos(IntEnum):
    DINHEIRO = 1
    DÉBITO = 2
    CRÉDITO = 3
    PIX = 4