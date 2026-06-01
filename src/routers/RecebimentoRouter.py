#Peterson Wiggers
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
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
    id: Optional[int] = Query(None, description="Filtrar por ID"),
    nome: Optional[str] = Query(None, description="Filtrar por nome"),
    matricula: Optional[str] = Query(None, description="Filtrar por matrícula"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF"),
    grupo: Optional[str] = Query(
        None,
        description="Filtrar por grupo: 1=Admin, 2=Balcão, 3=Caixa - Separar por vírgula",
    ),
    telefone: Optional[str] = Query(None, description="Filtrar por telefone"),
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1])),
):
    try:
        query = select(FuncionarioDB)
        
        # Aplicar filtros
        if id is not None:
            query = query.where(FuncionarioDB.id == id)
        if nome is not None:
            query = query.where(FuncionarioDB.nome.ilike(f"%{nome}%"))  # ilike = case insensitive
        if matricula is not None:
            query = query.where(FuncionarioDB.matricula == matricula)
        if cpf is not None:
            query = query.where(FuncionarioDB.cpf == cpf)
        if grupo is not None:
            # Converter string separada por vírgula para lista de inteiros
            grupos_list = [int(g.strip()) for g in grupo.split(',') if g.strip().isdigit()]
            query = query.where(FuncionarioDB.grupo.in_(grupos_list))
        if telefone is not None:
            query = query.where(FuncionarioDB.telefone.ilike(f"%{telefone}%"))

        # Aplicar paginação
        result = await db.execute(query.offset(skip).limit(limit))
        funcionarios = result.scalars().all()
        return funcionarios
    except RateLimitExceeded:
        # Propagar exceção original para o handler personalizado
        raise
    except Exception as e:
        # Apenas erros reais da aplicação (não rate limit)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar funcionários: {str(e)}",
        )

