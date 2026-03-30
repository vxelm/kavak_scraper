from sqlmodel import SQLModel, create_engine
from src.settings import DATABASE_URL

#echo=False NO imprimir en consola.
engine = create_engine(DATABASE_URL, echo=False)

def create_db_n_tables():
    SQLModel.metadata.create_all(engine)