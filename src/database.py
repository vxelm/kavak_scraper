from sqlmodel import SQLModel, create_engine
from src.settings import build_url_db
from src.models import Auto, FinancialPlan

_engine = None
def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(build_url_db(), echo=False) #echo=False NO imprimir en consola.

    return _engine

def create_db_n_tables():
    SQLModel.metadata.create_all(get_engine())