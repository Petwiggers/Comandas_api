#Peterson Wiggers
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from infra.orm.ClienteModel import ClienteDB
from infra.orm.ComandaModel import ComandaDB, ComandaProdutoDB
from infra.orm.ProdutoModel import ProdutoDB
from infra.orm.FuncionarioModel import FuncionarioDB
from infra.orm.ClienteModel import ClienteDB
from services.AuditoriaService import AuditoriaService

# Domain Schemas
from domain.schemas.RecebimentoSchema import (
    ComprovanteRecebimento,
    RecebimentoCompletoRequest,
    RecebimentoCompletoResponse,
    RecebimentoDashboardItem,
    RecebimentoComandasDetalheResponse,
)
from domain.schemas.AuthSchema import FuncionarioAuth
from domain.schemas.ClienteSchema import ClienteResponse
from domain.schemas.FuncionarioSchema import FuncionarioResponse
from domain.schemas.ComandaSchema import ComandaResponse

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
                ClienteDB.id.label("cliente_id"),
                ClienteDB.nome.label("cliente_nome"),
                func.coalesce(func.sum(ComandaProdutoDB.quantidade * ComandaProdutoDB.valor_unitario), 0).label("total"),
                func.coalesce(func.sum(ComandaProdutoDB.quantidade), 0).label("quantidade_produtos"),
            )
            .join(ComandaProdutoDB, ComandaProdutoDB.comanda_id == ComandaDB.id, full=True)
            .join(ClienteDB, ClienteDB.id == ComandaDB.cliente_id, full=True)
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
                cliente=row.cliente_nome if row.cliente_nome else None,
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


@router.get(
    "/recebimento/comandas/detalhe/{comandas_ids}",
    response_model=RecebimentoComandasDetalheResponse,
    tags=["Recebimento"],
    status_code=status.HTTP_200_OK,
    summary="Detalhar comandas selecionadas para visualização antes do pagamento",
)
@limiter.limit(get_rate_limit("moderate"))
async def get_detalhe_comandas(
    request: Request,
    comandas_ids: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user),
):
    try:
        ids = [int(id_) for id_ in comandas_ids.split(",") if id_.strip()]
        if not ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="IDs das comandas obrigatórios.",
            )

        comandas_query = (
            select(
                ComandaDB.id,
                ComandaDB.comanda,
                ComandaDB.status,
                ComandaDB.data_hora,
                ComandaDB.cliente_id,
                ComandaDB.funcionario_id,
            )
            .where(ComandaDB.id.in_(ids))
        )
        comandas_result = await db.execute(comandas_query)
        lista_comandas = comandas_result.all()
        if any(row.status != 0 for row in lista_comandas):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Todas as comandas devem estar com status 0 (abertas).",
            )
        comandas = {row.id: row for row in lista_comandas}

        produtos_query = (
            select(
                ComandaProdutoDB.id,
                ComandaProdutoDB.comanda_id,
                ComandaProdutoDB.produto_id,
                ComandaProdutoDB.quantidade,
                ComandaProdutoDB.valor_unitario,
                ProdutoDB.nome.label("produto_nome"),
                ProdutoDB.descricao.label("produto_descricao"),
                ProdutoDB.foto.label("produto_foto"),
                ProdutoDB.valor_unitario.label("produto_valor_unitario"),
            )
            .join(ProdutoDB, ProdutoDB.id == ComandaProdutoDB.produto_id)
            .where(ComandaProdutoDB.comanda_id.in_(ids))
        )
        produtos_result = await db.execute(produtos_query)
        produtos = produtos_result.all()

        detalhamento = {}
        total_geral = 0.0
        quantidade_total = 0

        for row in produtos:
            total_item = float(row.quantidade) * float(row.valor_unitario)
            total_geral += total_item
            quantidade_total += int(row.quantidade)

            item = {
                'id': row.id,
                "produto_id": row.produto_id,
                "produto": row.produto_nome,
                "quantidade": int(row.quantidade),
                "valor_unitario": float(row.valor_unitario),
                "total_item": total_item,
            }
            detalhamento.setdefault(row.comanda_id, []).append(item)

        comandas_detalhes = []
        for comanda_id in ids:
            comanda_row = comandas[comanda_id]
            itens = detalhamento.get(comanda_id, [])
            subtotal = sum(item["total_item"] for item in itens)

            comandas_detalhes.append(
                {
                    "id": comanda_row.id,
                    "comanda": comanda_row.comanda,
                    "itens": itens,
                    "subtotal": float(subtotal),
                    "quantidade_total": sum(item["quantidade"] for item in itens),
                }
            )

        return {
            "comandas": comandas_detalhes,
            "total_geral": float(total_geral),
            "quantidade_total": int(quantidade_total),
        }
    except RateLimitExceeded:
        raise
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar detalhes das comandas: {str(e)}",
        )

@router.post(
    "/recebimento/complete",
    response_model=RecebimentoCompletoResponse,
    tags=["Recebimento"],
    status_code=status.HTTP_201_CREATED,
    summary="Confirmar pagamento e criar recebimento completo, protegida por JWT e grupo 1",
)
@limiter.limit(get_rate_limit("moderate"))
async def post_recebimento_complete(
    request: Request,
    recebimento_data: RecebimentoCompletoRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user),
):
    try:
        if not recebimento_data.comandas_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma comanda informada.",
            )

        # Buscar todas as comandas
        comandas_query = (
            select(ComandaDB)
            .where(ComandaDB.id.in_(recebimento_data.comandas_ids))
        )
        comandas_result = await db.execute(comandas_query)
        comandas = comandas_result.scalars().all()

        if len(comandas) != len(set(recebimento_data.comandas_ids)):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Uma ou mais comandas não foram encontradas.",
            )

        # Buscar todos os produtos das comandas
        produtos_query = (
            select(
                ComandaProdutoDB.id,
                ComandaProdutoDB.comanda_id,
                ComandaProdutoDB.produto_id,
                ComandaProdutoDB.quantidade,
                ComandaProdutoDB.valor_unitario,
            )
            .where(ComandaProdutoDB.comanda_id.in_(recebimento_data.comandas_ids))
        )
        produtos_result = await db.execute(produtos_query)
        produtos = produtos_result.all()

        # Calcular totais
        subtotal_geral = sum(float(row.quantidade) * float(row.valor_unitario) for row in produtos)
        desconto_total = float(recebimento_data.desconto_valor or 0)
        acrescimo_total = float(recebimento_data.acrescimo_valor or 0)
        valor_final = subtotal_geral - desconto_total + acrescimo_total

        # Criar recebimento
        recebimento = RecebimentoDB(
            id=None,
            funcionario_id=recebimento_data.funcionario_id,
            cliente_id=recebimento_data.cliente_id,
            subtotal_geral=subtotal_geral,
            desconto_total=desconto_total,
            acrescimo_total=acrescimo_total,
            valor_final=valor_final,
        )
        db.add(recebimento)
        await db.flush()  # Obtém o ID gerado

        # Criar vínculos recebimento-comanda
        for comanda_id in recebimento_data.comandas_ids:
            vinculo = RecebimentoComandaDB(
                id=None,
                recebimento_id=recebimento.id,
                comanda_id=comanda_id,
            )
            db.add(vinculo)

        # Atualizar status das comandas para 1 (fechada)
        update_query = (
            select(ComandaDB)
            .where(ComandaDB.id.in_(recebimento_data.comandas_ids))
        )
        result = await db.execute(update_query)
        comandas_para_atualizar = result.scalars().all()
        
        for comanda in comandas_para_atualizar:
            comanda.status = 1

        # Commit da transação
        await db.commit()
        await db.refresh(recebimento)

        # Buscar dados para retorno
        funcionario_query = select(FuncionarioDB).where(FuncionarioDB.id == recebimento_data.funcionario_id)
        funcionario_result = await db.execute(funcionario_query)
        funcionario = funcionario_result.scalar()

        if not funcionario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Funcionário responsável não encontrado.",
            )
        if funcionario.grupo not in [1, 3]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Somente funcionários Admin ou Caixa têm permissão para realizar recebimentos.",
            )

        cliente = None
        if recebimento_data.cliente_id:
            cliente_query = select(ClienteDB).where(ClienteDB.id == recebimento_data.cliente_id)
            cliente_result = await db.execute(cliente_query)
            cliente = cliente_result.scalar()

        # Construir resposta
        funcionario_response = FuncionarioResponse.model_validate(funcionario)
        cliente_response = ClienteResponse.model_validate(cliente) if cliente else None

        comandas_pagas = [ComandaResponse.model_validate(comanda) for comanda in comandas_para_atualizar]

        return RecebimentoCompletoResponse(
            sucesso=True,
            mensagem="Recebimento criado com sucesso",
            recebimento_id=recebimento.id,
            comandas_pagas=comandas_pagas,
            subtotal_geral=float(recebimento.subtotal_geral),
            desconto_total=float(recebimento.desconto_total),
            acrescimo_total=float(recebimento.acrescimo_total),
            valor_final=float(recebimento.valor_final),
            cliente=cliente_response,
            funcionario=funcionario_response,
            data_hora=recebimento.data_hora,
        )

    except RateLimitExceeded:
        raise
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar recebimento: {str(e)}",
        )
