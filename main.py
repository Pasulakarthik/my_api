from fastapi import FastAPI, Depends , HTTPException ,status,Query
from sqlalchemy.orm import Session
import model , schemas ,password
from database import get_db
from datetime import timedelta , datetime
from jose import JWTError , jwt
from fastapi.security import OAuth2PasswordRequestForm , OAuth2PasswordBearer
from datetime import timedelta

SECRET_KEY = "tINXBSTA0iXAlSyBsoAzJK8BuDtbZRF2OEONJbh7yEw"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    data.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)




app = FastAPI()

@app.get("/products")
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

#!--------User----------


@app.post("/register",tags=["signin"])
def register(user:schemas.UserCreate,db:Session = Depends(get_db)):
    existing = db.query(model.User).filter(model.User.email == user.email).first()
    if not user:
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
        role : str = payload.get("role")

        if name is  None or role is None:
            raise credential_exception
        
    except JWTError:
        raise credential_exception
    
    user = db.query(model.User).filter(model.User.name == name).first()

    if user is None:
        raise HTTPException(status_code=401,detail="User not found")
    
    return {"name":name, "role":role}

@app.get("/me",tags=["signin"])
def protected_route(current_user: dict = Depends(current_user)):
    return {"mes":f"Hello, {current_user['name']} | You accessed a protected route"}




def require_roles(allowed_roles:list[str]):
    def role_check(current_user: dict = Depends(current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Not enough permission")
        
        return current_user
    return role_check


@app.get("/profile",tags=["signin"])
def profile(current_user: dict =Depends(require_roles(["user","admin"]))):
    return{"msg":f"Profile of {current_user['name']} ({current_user['role']})"}


def admin_only(current_user: model.User = Depends(current_user)):
    if current_user['role'] != "admin":
        raise HTTPException(status_code=403,detail="Admin only")
    
    return current_user

@app.get("/admin",tags=["signin"])
def get_all_users_and_admins(user : model.User = Depends(admin_only),db:Session = Depends(get_db)):

    return db.query(model.User).all()


@app.delete("/admin/{email}",tags=["signin"])
def delete(email:str, db:Session = Depends(get_db),current_user: model.User = Depends(current_user)):

    if current_user['role'] != "admin":
        raise HTTPException(status_code=403,detail="Admin only")
    
    user = db.query(model.User).filter(model.User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=401,detail="User not found")
        
    db.delete(user)
    db.commit()
    return {"message":"Removed Successful"}


#!--------Store----------


@app.post("/admin/{email}", response_model=schemas.ProductOut,tags=["Store"])
def add_product(email:str,product:schemas.ProductCreate, db: Session = Depends(get_db),current_user: model.User = Depends(current_user)):

    if current_user['role'] != "admin":
        raise HTTPException(status_code=403,detail="Admin only")
    
    user = db.query(model.User).filter(model.User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=401,detail="User not found")

    new = model.Product(
        name = product.name,
        price = product.price,
        brand = product.brand
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

    db.commit()
    return {"msg": "Product updated"}


@app.delete("/admin/{email}",tags=["Store"])
def delete_product(email:str,product_id: int, db: Session = Depends(get_db),current_user: model.User = Depends(current_user)):

    if current_user['role'] != "admin":
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

