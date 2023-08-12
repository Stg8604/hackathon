from fastapi import FastAPI, Depends,  HTTPException, status,Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Annotated
from datetime import datetime,timedelta
#from jose import JWTError,jwt
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
import mysql.connector
from mysql.connector import connect,Error
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Stg08604",
  database="hackathon",
   port='3306'
)
app=FastAPI()
@app.post("/createtable/")
async def create_table(listname:Annotated[str,Form()]):
    cursor=mydb.cursor()
    selectstatement="create table {}(emtpy varchar(30))".format(listname)
    cursor.execute(selectstatement)
    mydb.commit()
@app.post("/addcolumns/")
async def add_columns(listname:Annotated[str,Form()],columnname:Annotated[str,Form()],columntype:Annotated[str,Form()],constraint:Annotated[str,Form()]|None=None,defvalue:Annotated[str,Form()]|None=None,index:Annotated[str,Form()]|None=None):
    cursor=mydb.cursor()
    selectstatement="alter table {} add column {} {}".format(listname,columnname,columntype)
    cursor.execute(selectstatement)
    cursor=mydb.cursor()
    try:
        selectstatement="alter table {} add column {} {}".format(listname,columnname,columntype)
        cursor.execute(selectstatement)
    except:
        pass
    cursor=mydb.cursor()
    if(constraint=="not null"):
        selectstatement="alter table {} modify {} {} NOT NULL".format(listname,columnname,columntype)
        cursor.execute(selectstatement)
        cursor.close()
    elif(constraint=="unique"):
        selectstatement="alter table {} add UNIQUE({})".format(listname,columnname)
        cursor.execute(selectstatement)
        cursor.close()
    elif(constraint=="default"):
        selectstatement="alter table {} add constraint {} default %s".format(listname,columnname)
        values=(defvalue,)
        cursor.execute(selectstatement,values)
        cursor.close()
    elif(constraint=="Index"):
        selectstatement="create INDEX {} on {}({})".format(index,listname,columnname)
        cursor.execute(selectstatement)
        cursor.close()
    elif(constraint=="Primary Key"):
        selectstatement="alter table {} add PRIMARY KEY({})".format(listname,columnname)
        cursor.execute(selectstatement)
        cursor.close()
    mydb.commit()
@app.get("/showtables/")
async def show_table():
    cursor=mydb.cursor()
    selectstatement="show tables"
    cursor.execute(selectstatement)
    pb=list()
    for i in cursor.fetchall():
        pb.append(i[0])
    return pb
@app.post("/deletetable/")
async def delete_table(listname:Annotated[str,Form()]):
    cursor=mydb.cursor()
    selectstatement="drop table {}".format(listname)
    cursor.execute(selectstatement)
    cursor.close()
    mydb.commit()
@app.post("/showcolumns/")
async def show_columns(listname:Annotated[str,Form()]):
    cursor=mydb.cursor()
    selectstatement="show columns from {}".format(listname)
    cursor.execute(selectstatement)
    pb=list()
    for i in cursor.fetchall():
        if(i[0]!="emtpy"):
            pb.append(i[0])
    cursor.close()
    return pb
#((data1,data2,..),(data,...))
@app.post("/showdata/")
async def show_data(listname:Annotated[str,Form()]):
    cursor=mydb.cursor()
    selectstatement="select * from {}".format(listname)
    cursor.execute(selectstatement)
    result1=cursor.fetchall()
    cursor=mydb.cursor()
    selectstatement="show columns from {}".format(listname)
    cursor.execute(selectstatement)
    result2=cursor.fetchall()
    pb=list()
    for i in cursor.fetchall():
        if(i[0]!="emtpy"):
            pb.append(i[0])
    pb2=list()
    for i in result1:
        dictor=dict()
        j=0
        while j<len(i):
            dictor[pb[j]]=i[j]
        pb2.append(dictor)
    return pb2
