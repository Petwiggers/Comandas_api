#Peterson Wiggers
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from infra.orm.ComandaModel import ComandaDB, ComandaProdutoDB
from services.AuditoriaService import AuditoriaService

# Domain Schemas
from domain.schemas.RecebimentoSchema import (
ComprovanteRecebimento,
RecebimentoCompletoRequest,
RecebimentoCompletoResponse,
RecebimentoDashboardItem
)
from domain.schemas.AuthSchema import FuncionarioAuth

# Infra
from infra.orm.RecebimentoComandaModel import RecebimentoComandaDB
from infra.orm.RecebimentoModel import RecebimentoDB
from infra.database import get_async_db
from infra.security import get_password_hash
from infra.dependencies import get_current_active_user, require_group
from infra.rate_limit import get_rate_limit, limiter 

from slowapi.errors import RateLimitExceeded

router = APIRouter()

@router.get(
    "/recebimento/dashboard",
    response_model=List[RecebimentoDashboardItem],
    tags=["Recebimento"],
    status_code=status.HTTP_200_OK,
    summary="Listar itens para o dashboard de recebimento - protegida por JWT e grupo 1",
)
@limiter.limit(get_rate_limit("moderate"))
async def get_recebimento_dashboard(
   request: Request,
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user),
):
    try:
        comandas_query = (
            select(
                ComandaDB.id,
                ComandaDB.comanda,
                ComandaDB.status,
                ComandaDB.data_hora,
                func.coalesce(func.sum(ComandaProdutoDB.quantidade * ComandaProdutoDB.valor_unitario), 0).label("total"),
                func.coalesce(func.sum(ComandaProdutoDB.quantidade), 0).label("quantidade_produtos"),
            )
            .join(ComandaProdutoDB, ComandaProdutoDB.comanda_id == ComandaDB.id)
            .where(ComandaDB.status == 0)
            .group_by(ComandaDB.id, ComandaDB.comanda, ComandaDB.status, ComandaDB.data_hora)
            .offset(skip)
            .limit(limit)
        )
        comandas_result = await db.execute(comandas_query)
        rows = comandas_result.all()

        dashboard_items = [
            RecebimentoDashboardItem(
                id=row.id,
                comanda=row.comanda,
                status=row.status,
                cliente=None,
                total=float(row.total),
                quantidade_produtos=int(row.quantidade_produtos),
                data_hora=row.data_hora,
            )
            for row in rows
        ]

        return dashboard_items
    except RateLimitExceeded:
        # Propagar exceção original para o handler personalizado
        raise
    except Exception as e:
        # Apenas erros reais da aplicação (não rate limit)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar funcionários: {str(e)}",
        )

