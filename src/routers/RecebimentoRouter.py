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

