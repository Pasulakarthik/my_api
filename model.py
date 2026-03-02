from sqlalchemy import Column, Integer , String, Boolean,ForeignKey
from database import Base

class User(Base):
    __tablename__ = "table"

    id = Column(Integer, primary_key=True,index=True)
    name = Column(String)
    email = Column(String,unique=True,index=True)
    hashed_password = Column(String)
    role = Column(String,default="user")

class Product(Base):
    __tablename__ = "Products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    brand = Column(String, nullable=False)


class Cart(Base):
    __tablename__ = "cart"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("table.id"))
    product_id = Column(Integer,ForeignKey("Products.id"))
    quantity = Column(Integer,default=1)