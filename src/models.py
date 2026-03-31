from sqlmodel import Field, SQLModel,Relationship
from datetime import date
from typing import Optional

class FinancialPlan(SQLModel, table=True):
    #PK autoincremental
    id: int | None = Field(default=None, primary_key=True)
    
    #Llave foranea apuntando a tabla 'auto'
    id_auto: str = Field(foreign_key="auto.id")
    
    #Datos del negocio
    precio: int | None
    tasa_servicio: float
    plazo: int
    mensualidad: int | None
    tasa_interes: float | None 
    seguro: float | None
    enganche_simulado: float
    enganche_min: float
    enganche_max: float

    fecha_captura: date = Field(default_factory=date.today)

    #Relacion el 'auto' al que pertenece este plan
    auto: "Auto" = Relationship(back_populates="planes")


class Auto(SQLModel, table=True):
    #NO nulos NO Nones
    id: str = Field(primary_key=True)
    slug: str
    city: str

    #Datos necesarios para el negocio
    price: int | None
    year: int 
    km: int 

    #Datos que pueden ser nulos o vacios
    gear: str | None = None
    discount_offer: bool = Field(default=False)
    is_reserved: bool = Field(default=False)    
    details: Optional[str] | None = None

    #Lista de planes financieros que pertenecen al auto
    planes: list[FinancialPlan] = Relationship(back_populates="auto")