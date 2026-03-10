#Peterson Wiggers
from fastapi import APIRouter
from domain.schemas.ProdutoSchema import ProdutoCreate, ProdutoUpdate, ProdutoResponse
router = APIRouter()
# Criar as rotas/endpoints: GET, POST, PUT, DELETE
@router.get("/produto/", tags=["Produto"], status_code=200)
async def get_produto():
    return {"msg": "produto get todos executado"}

@router.get("/produto/{id}", tags=["Produto"], status_code=200)
async def get_produto(id: int):
    return {"msg": "produto get um executado"}

@router.post("/produto/", tags=["Produto"], status_code=200)
async def post_produto(corpo: ProdutoCreate):
    return {"msg": "produto post executado", "nome": corpo.nome, "descrição": corpo.descricao, "valor": corpo.valor_unitario}

@router.put("/produto/{id}", tags=["Produto"], status_code=200)
async def put_produto(id: int, corpo: ProdutoUpdate):
    return {"msg": "produto put executado", "nome": corpo.nome, "descrição": corpo.descricao, "valor": corpo.valor_unitario}

@router.delete("/produto/{id}", tags=["Produto"], status_code=200)
async def delete_produto(id: int):
    return {"msg": "produto delete executado", "id":id}