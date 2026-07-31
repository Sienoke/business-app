from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api import company, bank

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Business Accounting MVP", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(company.router, prefix="/api/company", tags=["Company"])
app.include_router(bank.router, prefix="/api/bank", tags=["Bank"])

@app.get("/")
def root():
    return {"message": "Business Accounting API is running"}

from app.api import company, bank, employees
...
app.include_router(employees.router, prefix="/api/employees", tags=["Employees"])
