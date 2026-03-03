from pydantic import BaseModel,EmailStr

#!-----------User------------


class UserCreate(BaseModel):
    name : str
    email :EmailStr
    password: str
    role: str

class UserLogin(BaseModel):
    name : str
    password: str



#!-----------Store------------


class ProductCreate(BaseModel):
    name: str
    price: int
    brand: str
    stock: int


class ProductIn(BaseModel):
    name: str
    price: int
    brand: str
    stock: int
    
class ProductOut(ProductCreate):
    id: int

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: str
    price: int
    brand: str
    stock: int

