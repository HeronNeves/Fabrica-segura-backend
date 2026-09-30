from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DadosSensorCreate(BaseModel):
    temperatura: float
    chama_detectada: bool
    localizacao: Optional[str] = "Galpão Principal"

class DadosSensorResponse(BaseModel):
    id: int
    temperatura: float
    chama_detectada: bool
    localizacao: str
    data_hora: datetime

    class Config:
        from_attributes = True