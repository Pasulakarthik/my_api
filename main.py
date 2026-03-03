from fastapi import FastAPI, Depends , HTTPException ,status,Query , BackgroundTasks
from typing import Optional
from sqlalchemy.orm import Session
import model , schemas ,password
from database import get_db , engine
from datetime import timedelta , datetime
from jose import JWTError , jwt
from fastapi.security import OAuth2PasswordRequestForm , OAuth2PasswordBearer
from datetime import timedelta
import logging , time


SECRET_KEY = "tINXBSTA0iXAlSyBsoAzJK8BuDtbZRF2OEONJbh7yEw"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)




app = FastAPI()

# model.Base.metadata.create_all(bind=engine)

def send_email(email:str):
    logging.info(f"Sending welcome email to {email}")

@app.get("/product")
def get_products(
    page:int = Query(1, ge=1),
    size:int = Query(10,ge=1,le=50),
    db:Session = Depends(get_db)
):
    skip = (page - 1)*size

    notes = db.query(model.Product).offset(skip).limit(size).all()
    total = db.query(model.Product).count()

    return {
        "page":page,
        "size":size,
        "total_records":total,
        "total_pages":(total + size - 1) // size,
        "data":notes

    }

@app.get("/product",tags=['filter'])
def filter_product(
    min_price:Optional[int] = Query(None),
    max_price:Optional[int] = Query(None),
    brand :Optional[str] = Query(None),
    db:Session = Depends(get_db)
    ):
    query = db.query(model.Product)

    if max_price is not None:
        query = query.filter(model.Product.price >= max_price)

    if min_price is not None:
        query = query.filter(model.Product.price >= min_price)

    if brand :
        query = query.filter(model.Product.brand == brand)

    return query.all()

#!--------User----------


@app.post("/register",tags=["signin"])
def register(user:schemas.UserCreate ,background_tasks:BackgroundTasks ,db:Session = Depends(get_db)):
    existing = db.query(model.User).filter(model.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hash_password = password.hash_password(user.password)
    
    new_user = model.User(
        name= user.name,
        email= user.email,
        hashed_password= hash_password,
        role =  user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    background_tasks.add_task(send_email, user.email)

    return {"id":new_user.id , "name": new_user.name ,"email": new_user.email , "role": new_user.role}


@app.post("/login",tags=["signin"])
def login(form_data: OAuth2PasswordRequestForm = Depends(),db:Session = Depends(get_db)):
    user = db.query(model.User).filter(model.User.name == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not password.pass_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Password")
    

    token_data = {"sub":user.name , "role":user.role}
    token = create_access_token(token_data)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


Oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def current_user(token:str= Depends(Oauth2_scheme) , db:Session = Depends(get_db)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="could not validate credential",headers={"www-Authenticate": "Bearer"})

    try:
        payload = jwt.decode(token , SECRET_KEY,algorithms=[ALGORITHM])
        name : str= payload.get("sub")

        if name is  None:
            raise credential_exception
        
    except JWTError:
        raise credential_exception
    
    user = db.query(model.User).filter(model.User.name == name).first()

    if user is None:
        raise HTTPException(status_code=401,detail="User not found")
    
    return user

@app.get("/me",tags=["signin"])
def protected_route(current_user: dict = Depends(current_user)):
    return {"mes":f"Hello, {current_user['name']} | You accessed a protected route"}




def require_roles(allowed_roles:list[str]):
    def role_check(current_user: model.User = Depends(current_user)):
        user_role = current_user.role
        if user_role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not enough permission")
        
        return current_user
    return role_check


@app.get("/profile",tags=["signin"])
def profile(current_user: dict =Depends(require_roles(["user","admin"]))):
    return{"msg":f"Profile of {current_user.name} ({current_user.role})"}


def admin_only(current_user: model.User = Depends(current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403,detail="Admin only")
    
    return current_user

@app.get("/admin",tags=["signin"])
def get_all_users_and_admins(user : model.User = Depends(admin_only),db:Session = Depends(get_db)):

    return db.query(model.User).all()


@app.delete("/Delete_User/{email}",tags=["signin"])
def delete(id:int, db:Session = Depends(get_db),current_user: model.User = Depends(current_user)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403,detail="Admin only")
    
    user = db.query(model.User).filter(model.User.id == id).first()
    
    if not user:
        raise HTTPException(status_code=401,detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"message":"Removed Successful"}


#!--------Store----------


@app.post("/admin/{email}", response_model=schemas.ProductOut,tags=["Store"])
def add_product(email:str,product:schemas.ProductCreate, db: Session = Depends(get_db),current_user: model.User = Depends(current_user)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403,detail="Admin only")
    
    user = db.query(model.User).filter(model.User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=401,detail="User not found")

    new = model.Product(
        name = product.name,
        price = product.price,
        brand = product.brand,
        stock = product.stock
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


@app.get("/product/{product_id}", response_model=schemas.ProductOut,tags=["Store"])
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    product = db.query(model.Product).filter(model.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products",tags=["Store"])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(model.Product).all()


@app.put("/product/{product_id}",tags=["Store"])
def update_product(product_id: int, data: schemas.ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(model.Product).filter(model.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.name = data.name
    product.price = data.price
    product.brand = data.brand
    product.stock = data.stock

    db.commit()
    return {"msg": "Product updated"}


@app.delete("/admin/{email}",tags=["Store"])
def delete_product(email:str,product_id: int, db: Session = Depends(get_db),current_user: model.User = Depends(current_user)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403,detail="Admin only")
    
    user = db.query(model.User).filter(model.User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=401,detail="User not found")
    
    product = db.query(model.Product).filter(model.Product.id == product_id).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"msg": "Product deleted"}

#!---------------Shopping------------------

@app.post("/AddToCart/{quantity}",tags=['shopping'])
def AddToCart(quantity:int,product_id:int,db:Session = Depends(get_db), current_user: model.User = Depends(current_user)):
    product = db.query(model.Product).filter(model.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock < quantity:
        raise HTTPException(status_code=400,detail="Insufficient stock")
    
    new = model.Cart(
        name = product.name,
        brand = product.brand,
        price = product.price,
        quantity = quantity,
        user_id = current_user.id,
        Product_id = product.id
        )
    db.add(new)
    db.commit()
    db.refresh(new)

    return {
        'name' :product.name,
        'brand' : product.brand,
        'price' : product.price,
        'quantity': quantity,
        'user_id' : current_user.id,
        'Product_id' : product.id

    }


@app.get("/cart", tags=["shopping"])
def get_cart(
    db: Session = Depends(get_db),
    current_user: model.User = Depends(current_user)
):
    cart = db.query(model.Cart).filter(
        model.Cart.user_id == current_user.id
    ).all()

    if not cart:
        return {"message": "Cart is empty", "items": []}

    return cart

def order(email:str,current_user: model.User = Depends(current_user) ):
    logging.info(f"order placed by the user with  gmail {email}")

@app.post("/order",tags=['shopping'])
def Place_Order(quantity:int,product_id:int ,background_tasks:BackgroundTasks ,db:Session = Depends(get_db), current_user: model.User = Depends(current_user)):
    product = db.query(model.Product).filter(model.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.stock < quantity:
        raise HTTPException(status_code=400,detail="Insufficient stock")
    
    new = model.Order(
        name = product.name,
        brand = product.brand,
        price = product.price,
        quantity = quantity,
        user_id = current_user.id,
        Product_id = product.id
        )
    db.add(new)
    db.commit()
    db.refresh(new)

    background_tasks.add_task(order, current_user.email)


    return {
        'name' :product.name,
        'brand' : product.brand,
        'price' : product.price,
        'quantity': quantity,
        'user_id' : current_user.id,
        'Product_id' : product.id

    }


@app.get("/order", tags=["shopping"])
def get_orders(
    db: Session = Depends(get_db),
    current_user: model.User = Depends(current_user)
):
    order = db.query(model.Order).filter(
        model.Order.user_id == current_user.id
    ).all()

    if not order:
        return {"message": "No  Orders yet", "items": []}

    return order

