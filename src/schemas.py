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