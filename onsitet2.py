from fastapi import FastAPI, Depends,  HTTPException, status,Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Annotated
import bcrypt
from datetime import datetime,timedelta
#from jose import JWTError,jwt
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import connect,Error
from decouple import config
import os

# Get the value of a specific environment variable
db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')
secretkey=os.environ.get("secret_key")
algo=os.environ.get("algo")
mydb = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name,
    port=3306
)
cursor=mydb.cursor()
selectstatement="select * from newusers"
cursor.execute(selectstatement)
result=cursor.fetchall()
cursor.close()
db=dict()
access=30
class Token(BaseModel):
    access_token:str
    token_type:str
class TokenData(BaseModel):
    username:str or None=None
class UserS(BaseModel):
    username: str
    dommainname:str
    hashpass: str
#for reading operations,no hashpass is needed
class User(BaseModel):
    username:str
    dommainname:str
class UserINDB(User):
    hashpass:str

pwd_context=CryptContext(schemes=["bcrypt"],deprecated='auto')#hashes pass, bcrypt scheme does the hashing
oauth2=OAuth2PasswordBearer(tokenUrl="token")#used to authenticate using OAuth2
app=FastAPI()
def verify_pass(normalpass,hashpass):
        return pwd_context.verify(normalpass,hashpass)
def gethaspass(password):
    return pwd_context.hash(password)
for i in result:
   if(i[2]!="Null"):
        db[i[0]]={"username":i[0],"dommainname":i[1],"hashpass":gethaspass(i[2])}
def getuser(db,username:str):
    if username in db:
        userdata=db[username]
        return UserINDB(**userdata)
def authentication(db,username:str,password:str):
    cursor=mydb.cursor()
    selectstatement="select * from newusers"
    cursor.execute(selectstatement)
    result=cursor.fetchall()
    cursor.close()
    for i in result:
      if(i[2]!="Null"):
        db[i[0]]={"username":i[0],"dommainname":i[1],"hashpass":gethaspass(i[2])}
    user=getuser(db,username)
    if not user:
        return False
    if not verify_pass(password,user.hashpass):  
        return False
    return user
def accessing(data:dict,timeexpire:timedelta or None=None):
    encode=data.copy()#data copied
    #checking if expire time is there
    if timeexpire:
        expire=datetime.utcnow()+ timeexpire
    else:
        expire=datetime.utcnow()+timedelta(minutes=15)
    encode.update({"exp":expire})
    encode_jwt=jwt.encode(encode,secretkey,algorithm=algo)#secret key=associated with encode,used for checking
    return encode_jwt
async def getcurrent(token:str=Depends(oauth2)):#depends on authentication
         credexcept=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Unvalidated",headers="Authenticate:Bearer")
         try:
             #decodes the jwt token
             payload=jwt.decode(token,secretkey,algorithms=[algo])
             username:str=payload.get("sub")
             if username is None:
                 raise credexcept
             tokendata=TokenData(username=username)
         except InvalidTokenError:
            raise credexcept
         cursor=mydb.cursor()
         selectstatement="select * from newusers"
         cursor.execute(selectstatement)
         result=cursor.fetchall()
         cursor.close()
         for i in result:
           if(i[2]!="Null"):
            db[i[0]]={"username":i[0],"dommainname":i[1],"hashpass":gethaspass(i[2])}
         user=getuser(db,username=tokendata.username)
         if user is None:
             raise credexcept
         return user
@app.post("/token/",response_model=Token)
async def loginaccess(form_data:OAuth2PasswordRequestForm=Depends()):
    user=authentication(db,form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="incorrect",headers={"Authenticate":"Bearer"})
    access_token_expires=timedelta(minutes=access)
    accesstoken=accessing(data={"sub":user.username},timeexpire=access_token_expires)  
    return  {"access_token":accesstoken,"token_type":"bearer"}
@app.post("/new_user/")
async def newuser(credentials:Annotated[str, Form()],domainname:Annotated[str, Form()],password:Annotated[str,Form()]):
    cursor=mydb.cursor()
    selectstatement="select * from newusers"
    cursor.execute(selectstatement)
    result=cursor.fetchall()
    cursor.close()
    values=(credentials,domainname,bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()))
    for i in values:
            if i=="":
                raise HTTPException(status_code=400, detail="Details Inappropriate")
    for i in result:
            if(domainname+".xyz.com" in i):
                raise HTTPException(status_code=409, detail="Domain Name Exists")
    cursor=mydb.cursor()
    selectstatement="insert into newusers values(%s,%s,%s,%s)"
    values=(credentials,domainname+".xyz.com",password,"no")
    cursor.execute(selectstatement,values)
    cursor.close()
    mydb.commit()

@app.post("/new_route/")
async def newroute(routename:Annotated[str, Form()],current_user:User=Depends(getcurrent)):
    cursor=mydb.cursor()
    selectstatement="insert into newusers values(%s,%s,%s,%s)"
    values=(current_user.username,current_user.dommainname+"/"+routename,"Null","no")
    cursor.execute(selectstatement,values)
    result=cursor.fetchall()
    cursor.close()
    mydb.commit()
@app.post("/view_route/")
async def viewroute(current_user:User=Depends(getcurrent)):
    cursor=mydb.cursor()
    selectstatement="select domainname from newusers where password=%s and credentials=%s"
    values=("Null",current_user.username)
    cursor.execute(selectstatement,values)
    result=cursor.fetchall()
    cursor.close()
    return result
@app.post("/premium/")
async def premium(premium:Annotated[str, Form()],current_user:User=Depends(getcurrent)):
    cursor=mydb.cursor()
    if(premium=="yes"):
        selectstatement="select domainname from newusers where credentials=%s"
        values=(current_user.username,)
        cursor.execute(selectstatement,values)
        result=cursor.fetchall()
        print(result)
        for i in result:
            cursor=mydb.cursor()
            name=i[0]
            newname=name.replace(".xyz", "")
            selectstatement="update newusers set domainname=%s where credentials=%s and domainname=%s"        
            values=(newname,current_user.username,name)
            cursor.execute(selectstatement,values)
            cursor.close()
            cursor=mydb.cursor()
            selectstatement="update newusers set premium=%s where credentials=%s"        
            values=("yes",current_user.username)
            cursor.execute(selectstatement,values)
            cursor.close()
        mydb.commit()
@app.post("/view_users/")
async def viewusers():
    cursor=mydb.cursor()
    selectstatement="select domainname from newusers where password!=%s"
    values=("Null",)
    cursor.execute(selectstatement,values)
    result1=cursor.fetchall()
    return result1
