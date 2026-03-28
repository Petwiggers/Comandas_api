#Peterson Wiggers
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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

# Infra
from infra.orm.ProdutoModel import ProdutoDB
from infra.database import get_db
from infra.dependencies import get_current_active_user, require_group


router = APIRouter()
# Criar as rotas/endpoints: GET, POST, PUT, DELETE
@router.get("/produto/",response_model=List[ProdutoResponse], tags=["Produto"], status_code=status.HTTP_200_OK)
async def get_produto(
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)):
    
    """Retorna todos os Produtos"""
    try:
        produtos = db.query(ProdutoDB).all()
        return produtos
    except Exception as e:
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro ao buscar produtos: {str(e)}"
        )
        
@router.get("/produtoSemId_Valor/",response_model=List[ProdutoResponseSemId_Valor], tags=["Produto"], status_code=status.HTTP_200_OK)
async def get_produto(db: Session = Depends(get_db)):
    """Retorna todos os Produtos"""
    try:
        produtos = db.query(ProdutoDB).all()
        return produtos
    except Exception as e:
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro ao buscar produtos: {str(e)}"
        )


@router.get("/produto/{id}", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_200_OK)
async def get_produto(
    id: int, 
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(get_current_active_user)):
    
    """Retorna um produto específico pelo ID"""
    try:
        produto = db.query(ProdutoDB).filter(ProdutoDB.id == id).first()
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
async def post_produto(
    produto_data: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))):
    """Cria um novo produto"""
    try:
        # Verifica se já existe produto com este nome
        existing_produto = db.query(ProdutoDB).filter(ProdutoDB.nome == produto_data.nome).first()
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
        db.commit()
        db.refresh(novo_produto)
        return novo_produto
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar funcionário: {str(e)}"
        )

@router.put("/produto/{id}", response_model=ProdutoResponse, tags=["Produto"], status_code=status.HTTP_200_OK)
async def put_produto(
    id: int,
    produto_data: ProdutoUpdate,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))):
    
    """Atualiza um produto existente"""
    try:
        produto = db.query(ProdutoDB).filter(ProdutoDB.id == id).first()
        if not produto:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado"
            )
            
        # Verifica se está tentando atualizar para um nome que já existe
        if produto_data.nome and produto_data.nome != produto.nome:
            existing_produto = db.query(ProdutoDB).filter(ProdutoDB.nome == produto_data.nome).first()
            
            if existing_produto:
                raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Já existe um produto com este nome"
                )
            
        update_data = produto_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            print('\n')
            print(field, value)
            print('\n')
            setattr(produto, field, value)
        db.commit()
        db.refresh(produto)
        return produto
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar produto: {str(e)}"
        )

@router.delete("/produto/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Produto"], summary="Remover produto")
async def delete_produto(
    id: int,
    db: Session = Depends(get_db),
    current_user: FuncionarioAuth = Depends(require_group([1]))):
    """Remove um produto"""
    try:
        produto = db.query(ProdutoDB).filter(ProdutoDB.id == id).first()
        if not produto:
            raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
            )
        db.delete(produto)
        db.commit()
        return None
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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