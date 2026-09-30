import os
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status, Security, BackgroundTasks
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models, schemas, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="API FabricaSegura - TechDay", description="Backend de monitoramento IoT para prevenção de incêndios.", version="1.1.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
API_KEY_NAME = "X-IoT-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def validar_api_key(api_key: str = Security(api_key_header)):
    chave_esperada = os.getenv("API_SECRET_KEY", "MinhaChaveSuperSegura_2026_TechDay")
    if api_key != chave_esperada:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso Negado: Chave de API inválida.")
    return api_key

def notificar_equipe_emergencia(localizacao: str, temperatura: float, chama: bool):
    motivo = "FOGO DETECTADO" if chama else f"TEMPERATURA CRÍTICA: ({temperatura}°C)"
    print(" ALERTA CRÍTICO DE SISTEMA ")
    print(f" Local: {localizacao} ")
    print(f" Motivo: {motivo} ")

@app.get("/", tags=["Sistema"])
def home():
    return {"status": "API Online, protegida e conectada ao neonDB!"}

@app.post("/api/leituras", response_model=schemas.DadosSensorResponse, status_code=status.HTTP_201_CREATED, tags=["Sensores"])
def receber_dados_sensor(payload: schemas.DadosSensorCreate, background_tasks: BackgroundTasks, db: Session = Depends(database.get_db), _: str = Depends(validar_api_key)):

    try:
        nova_leitura = models.LeituraSensor(**payload.model_dump())
        db.add(nova_leitura)
        db.commit()
        db.refresh(nova_leitura)

        if payload.chama_detectada or payload.temperatura >= 45.0:
            background_tasks.add_task(notificar_equipe_emergencia, payload.localizacao, payload.temperatura, payload.chama_detectada)
        return nova_leitura
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Erro interno no servidor do banco de dados.")
    
@app.get("/api/leituras", response_model=List[schemas.DadosSensorResponse], tags=["Dashboard"])
def listar_historico(limite: int = 20, db: Session = Depends(database.get_db)):
    return db.query(models.LeituraSensor).order_by(models.LeituraSensor.data_hora.desc()).limit(limite).all()

@app.get("/api/dashboard/estatisticas", tags=["Dashboard"])
def obter_estatisticas_painel(db: Session = Depends(database.get_db)):
    total_registros = db.query(models.LeituraSensor).count()
    total_emergencias = db.query(models.LeituraSensor).filter(
        (models.LeituraSensor.chama_detectada == True)
      | (models.LeituraSensor.temperatura >= 45.0)).count()

    maior_temp = db.query(func.max(models.LeituraSensor.temperatura)).scalar() or 0.0
    ultima_leitura = db.query(models.LeituraSensor).order_by(models.LeituraSensor.data_hora.desc()).first()
    
    status_fabrica = "OPERACIONAL"
    if ultima_leitura and (ultima_leitura.chama_detectada or ultima_leitura.temperatura >= 45.0):
        status_fabrica = "EMERGÊNCIA"

    return {
        "status_geral_fabrica": status_fabrica,
        "total_leituras_processadas": total_registros,
        "total_alertas_disparados": total_emergencias,
        "temperatura_maxima_historica": round(maior_temp, 2),
        "aviso_fuso_horario": "As horas abaixo estão no padrão UTC (Londres). Subtraia 3 horas para o horário de Brasília.",
        "ultima_atualizacao": ultima_leitura.data_hora if ultima_leitura else None
    }