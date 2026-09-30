from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime
from sqlalchemy.sql import func
from database import Base

class LeituraSensor(Base):
    __tablename__ = "leituras_sensores"

    id = Column(Integer, primary_key=True, index=True)
    temperatura = Column(Float, nullable=False)
    chama_detectada = Column(Boolean, nullable=False)
    localizacao = Column(String, default="Galpão Principal")
    data_hora = Column(DateTime(timezone=True), server_default=func.now())