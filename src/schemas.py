from sqlmodel import Field, Session, SQLModel, create_engine, Relationship
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Autokavak(BaseModel):
    #NO nulos NO Nones
    id: str = Field(..., min_length=1, description="ID Unico del auto")
    slug: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)

    #Datos necesarios para el negocio
    price: int = Field(..., gt=0, description="El precio debe ser mayor a 0")
    year: int = Field(..., ge=2000, le=datetime.now().year + 1, description="Anio logico del vehiculo")
    km: int = Field(..., ge=0, description="Kilometraje no puede ser 0")

    #Datos que pueden ser nulos o vacios
    gear: Optional[str] = None
    discount_offer: int = Field(default=0, ge=0, le=1)
    details: Optional[str] = None



class PlanFinanciero(SQLModel, table=True):
    #PK autoincremental
    id: int | None = Field(default=None, primary_key=True)
    
    #Llave foranea apuntando a tabla 'auto'
    id_auto: str = Field(foreign_key="auto.id")
    
    #Datos del negocio
    precio: int
    tasa_servicio: float
    plazo: int
    mensualidad: int
    tasa_interes: float
    seguro: float
    enganche_simulado: float
    enganche_min: float
    enganche_max: float

    #Relacion el 'auto' al que pertenece este plan
    auto: "Auto" = Relationship(back_populates="planes")


class Auto(SQLModel, table=True):
    #NO nulos NO Nones
    id: str = Field(primary_key=True)
    slug: str
    city: str

    #Datos necesarios para el negocio
    price: int 
    year: int 
    km: int 

    #Datos que pueden ser nulos o vacios
    gear: str | None = None
    discount_offer: int = Field(default=0)
    details: Optional[str] | None = None

    #Lista de planes financieros que pertenecen al auto
    planes: list[PlanFinanciero] = Relationship(back_populates="auto")