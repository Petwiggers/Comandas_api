#Peterson Wiggers
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

import base64

from fastapi import APIRouter
from domain.schemas.ProdutoSchema import (
    ProdutoCreate,
    ProdutoUpdate,
    ProdutoResponse,
    ProdutoResponseSemId_Valor
    )
from domain.schemas.AuthSchema import FuncionarioAuth
from services.AuditoriaService import AuditoriaService

# Infra
from infra.orm.ProdutoModel import ProdutoDB
from infra.database import get_async_db
from infra.dependencies import get_current_active_user, require_group
from infra.rate_limit import get_rate_limit, limiter 


router = APIRouter()
# Criar as rotas/endpoints: GET, POST, PUT, DELETE
@router.get("/produto/",response_model=List[ProdutoResponse], tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_produto(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user),
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limite: int = Query(
        100, ge=1, le=1000, description="Limite de registros"
    )):
    
    """Retorna todos os Produtos"""
    try:
        result = await db.execute(
            select(ProdutoDB)
            .offset(skip)
            .limit(limite)
        )
        produtos = result.scalars().all()
        return produtos
    except Exception as e:
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro ao buscar produtos: {str(e)}"
        )
        
@router.get("/produtoSemId_Valor/",response_model=List[ProdutoResponseSemId_Valor], tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_produto(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
    skip: int = Query(0, ge=0, description="Número de registros para pular"),
    limite: int = Query(
        100, ge=1, le=1000, description="Limite de registros"
    )):
    """Retorna todos os Produtos"""
    try:
        result = await db.execute(
            select(ProdutoDB)
            .offset(skip)
            .limit(limite)
        )
        produtos = result.scalars().all()
        return produtos
    except Exception as e:
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro ao buscar produtos: {str(e)}"
        )


@router.get("/produto/{id}", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("moderate"))
async def get_produto(
    request: Request,
    id: int, 
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)):
    
    """Retorna um produto específico pelo ID"""
    try:
        result = await db.execute(select(ProdutoDB).where(ProdutoDB.id == id))
        produto = result.scalar_one_or_none()
        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
        return produto
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro ao buscar produto: {str(e)}"
        )


@router.post("/produto/", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_201_CREATED)
@limiter.limit(get_rate_limit("restrictive"))
async def post_produto(
    request: Request,
    produto_data: ProdutoCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))):
    """Cria um novo produto"""
    try:
        # Verifica se já existe produto com este nome
        result = await db.execute(select(ProdutoDB).where(ProdutoDB.nome == produto_data.nome))
        existing_produto = result.scalar_one_or_none()
        if existing_produto:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe um produto com este nome"
            )
        # Cria o novo produto
        novo_produto = ProdutoDB(
        id=None, # Será auto-incrementado
        nome=produto_data.nome,
        descricao=produto_data.descricao,
        foto=produto_data.foto,
        valor_unitario=produto_data.valor_unitario
        )
        
        db.add(novo_produto)
        await db.commit()
        await db.refresh(novo_produto)
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="CREATE",
            recurso="PRODUTO",
            recurso_id=novo_produto.id,
            dados_antigos=None,
            dados_novos=novo_produto, # Objeto SQLAlchemy com dados novos
            request=request # Request completo para capturar IP e user agent
            )
        return novo_produto
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar produto: {str(e)}"
        )

@router.put("/produto/{id}", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_200_OK)
@limiter.limit(get_rate_limit("restrictive"))
async def put_produto(
    request: Request,
    id: int,
    produto_data: ProdutoUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))):
    
    """Atualiza um produto existente"""
    try:
        result = await db.execute(select(ProdutoDB).where(ProdutoDB.id == id))
        produto = result.scalar_one_or_none()
        if not produto:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado"
            )
            
        # Verifica se está tentando atualizar para um nome que já existe
        if produto_data.nome and produto_data.nome != produto.nome:
            result = await db.execute(select(ProdutoDB).where(ProdutoDB.nome == produto_data.nome))
            existing_produto = result.scalar_one_or_none()
            
            if existing_produto:
                raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe um produto com este nome"
                )
        dados_antigos_obj = produto.__dict__.copy()
        update_data = produto_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            print('\n')
            print(field, value)
            print('\n')
            setattr(produto, field, value)
        await db.commit()
        await db.refresh(produto)
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="UPDATE",
            recurso="PRODUTO",
            recurso_id=produto.id,
            dados_antigos=dados_antigos_obj,
            dados_novos=produto
        )
        return produto
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar produto: {str(e)}"
        )

@router.delete("/produto/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Produto"], summary="Remover produto")
@limiter.limit(get_rate_limit("critical"))
async def delete_produto(
    request: Request,
    id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))):
    """Remove um produto"""
    try:
        result = await db.execute(select(ProdutoDB).where(ProdutoDB.id == id))
        produto = result.scalar_one_or_none()
        if not produto:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
            )
        await db.delete(produto)
        await db.commit()
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=current_user.id,
            acao="DELETE",
            recurso="PRODUTO",
            recurso_id=produto.id,
            dados_antigos=produto,
            dados_novos=None,
            request=request
            )
        return None
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro ao deletar produto: {str(e)}"
        )

# bytes para Base64 string (para enviar no JSON)
def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode('utf-8')

# Base64 string para bytes (para salvar no banco)
def base64_to_bytes(data: str) -> bytes:
    return base64.b64decode(data)