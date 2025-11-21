import pandas as pd
import joblib
import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from io import StringIO
from prophet import Prophet
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import secrets
from database import (
    create_user, authenticate_user, create_budget, get_user_budget,
    create_expense, get_user_expenses, get_expense_stats
)
from budget_utils import distribute_budget




MODEL_PATH = '../models/prophet_model.pkl'

# Pydantic models for auth
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember: Optional[bool] = False

class UserResponse(BaseModel):
    id: str
    name: str
    email: str

class AuthResponse(BaseModel):
    user: UserResponse
    token: str

class BudgetRequest(BaseModel):
    user_id: str
    budget_amount: float
    period: str  # Format: 'YYYY-MM'
    use_forecast: Optional[bool] = True
    preferences: Optional[dict] = None  # savings_percent, min_reserve

class CategoryAllocation(BaseModel):
    category: str
    amount: float
    percentage: float
    reason: str

class BudgetResponse(BaseModel):
    budget_amount: float
    period: str
    allocations: List[CategoryAllocation]

class SetBudgetRequest(BaseModel):
    user_id: str
    amount: float
    period: str  # Format: 'YYYY-MM'

class AddExpenseRequest(BaseModel):
    user_id: str
    category: str
    amount: float
    description: str
    date: str  # Format: 'YYYY-MM-DD'

class ExpenseResponse(BaseModel):
    id: int
    user_id: str
    category: str
    amount: float
    description: str
    date: str

class ExpenseStatsResponse(BaseModel):
    today: float
    week: float
    month: float
    largest: float
    by_category: dict

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://expense-tracker-blush-phi.vercel.app",
        "https://expense-tracker-git-main-suhaib-lones-projects.vercel.app",
        "https://expense-tracker-n22hciz7m-suhaib-lones-projects.vercel.app",
        "http://localhost:5173"
    ], # Or specify "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def train_model(data):
    model = Prophet()
    model.fit(data)
    return model


# Load and preprocess data
def load_and_preprocess_data(file_path):
    data = pd.read_csv(file_path)

    # Parse dates in the 'Date' column
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

    # Drop rows with invalid dates
    data = data.dropna(subset=['Date'])

    # Group by 'Date' and sum the values
    data_grouped = data.groupby('Date').sum().reset_index()

    # Fill missing dates with y=0
    full_date_range = pd.date_range(start=data_grouped['Date'].min(), end=data_grouped['Date'].max())
    data_grouped = data_grouped.set_index('Date').reindex(full_date_range, fill_value=0).reset_index()
    data_grouped.rename(columns={'index': 'Date'}, inplace=True)

    # Rename columns for Prophet compatibility
    data_grouped.rename(columns={'Date': 'ds', 'Amount': 'y'}, inplace=True)

    return data_grouped

# Authentication endpoints
@app.post("/api/auth/signup", response_model=AuthResponse, status_code=201)
async def signup(request: SignupRequest):
    """
    Register a new user with database storage and password hashing
    """
    try:
        # Create user in database (with hashed password)
        user_data = create_user(
            name=request.name,
            email=request.email,
            password=request.password,
            phone=request.phone
        )
        
        # Generate token (in production, use JWT with expiration)
        token = secrets.token_urlsafe(32)
        
        return AuthResponse(
            user=UserResponse(
                id=user_data['id'],
                name=user_data['name'],
                email=user_data['email']
            ),
            token=token
        )
    
    except ValueError as e:
        # Email already exists
        raise HTTPException(
            status_code=400,
            detail={"message": str(e), "errors": {"email": "This email is already registered"}}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": "An error occurred during registration"}
        )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Login existing user with database verification
    """
    # Authenticate user
    user_data = authenticate_user(request.email, request.password)
    
    if not user_data:
        raise HTTPException(
            status_code=401,
            detail={"message": "Invalid credentials"}
        )
    
    # Generate token (in production, use JWT with expiration)
    token = secrets.token_urlsafe(32)
    
    return AuthResponse(
        user=UserResponse(
            id=user_data['id'],
            name=user_data['name'],
            email=user_data['email']
        ),
        token=token
    )

# data = load_and_preprocess_data('../data/nwd.csv')

# if os.path.exists(MODEL_PATH):
#     print("Loading saved Prophet model...")
#     model = joblib.load(MODEL_PATH)
# else:
#     print("Training new Prophet model...")
#     model = Prophet()
#     model.fit(data)
#     joblib.dump(model, MODEL_PATH)

@app.post("/upload_csv")
async def upload_csv(file: UploadFile = File(...)):
    contents = await file.read()
    new_data = StringIO(contents.decode())
    new_data_grouped = load_and_preprocess_data(new_data)
    model = train_model(new_data_grouped)
    
    # Create a DataFrame for the next month's dates
    last_date = new_data_grouped['ds'].max()
    future_dates = pd.date_range(start=last_date, periods=30, freq='D')[1:]  # Next 30 days
    future_df = pd.DataFrame({'ds': future_dates})
    
    # Generate predictions for the next month
    forecast = model.predict(future_df)
    predictions = forecast[['ds', 'yhat']]
    predictions['ds'] = predictions['ds'].astype(str)  # Convert Timestamp to string
    
    response = {"predictions": predictions.to_dict(orient='records')}
    return JSONResponse(content=response)

@app.post("/api/budget/distribute", response_model=BudgetResponse)
async def distribute_budget_endpoint(request: BudgetRequest):
    """
    Smart budget distribution using Prophet forecasting and historical data
    """
    try:
        # Extract preferences
        preferences = request.preferences or {}
        savings_percent = preferences.get('savings_percent', 10.0)
        min_reserve = preferences.get('min_reserve', 500.0)
        
        # Call budget distribution logic
        result = distribute_budget(
            user_id=request.user_id,
            budget_amount=request.budget_amount,
            period=request.period,
            use_forecast=request.use_forecast,
            savings_percent=savings_percent,
            min_reserve=min_reserve
        )
        
        return BudgetResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Budget distribution failed: {str(e)}"}
        )

@app.post("/api/budget/set")
async def set_budget_endpoint(request: SetBudgetRequest):
    """
    Set user's budget amount
    """
    try:
        user_id = int(request.user_id)
        budget = create_budget(user_id, request.amount, request.period)
        return {"success": True, "budget": budget}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to set budget: {str(e)}"}
        )

@app.get("/api/budget/get/{user_id}/{period}")
async def get_budget_endpoint(user_id: str, period: str):
    """
    Get user's budget for a period
    """
    try:
        budget = get_user_budget(int(user_id), period)
        if not budget:
            return {"success": False, "budget": None}
        return {"success": True, "budget": budget}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to get budget: {str(e)}"}
        )

@app.post("/api/expenses/add", response_model=ExpenseResponse)
async def add_expense_endpoint(request: AddExpenseRequest):
    """
    Add a new expense
    """
    try:
        user_id = int(request.user_id)
        expense = create_expense(
            user_id=user_id,
            category=request.category,
            amount=request.amount,
            description=request.description,
            date=request.date
        )
        return ExpenseResponse(
            id=expense['id'],
            user_id=str(expense['user_id']),
            category=expense['category'],
            amount=expense['amount'],
            description=expense['description'],
            date=expense['date']
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to add expense: {str(e)}"}
        )

@app.get("/api/expenses/list/{user_id}")
async def list_expenses_endpoint(user_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None):
    """
    Get user's expenses
    """
    try:
        expenses = get_user_expenses(int(user_id), start_date, end_date)
        return {"success": True, "expenses": expenses}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to get expenses: {str(e)}"}
        )

@app.get("/api/expenses/stats/{user_id}", response_model=ExpenseStatsResponse)
async def get_expense_stats_endpoint(user_id: str):
    """
    Get expense statistics
    """
    try:
        stats = get_expense_stats(int(user_id))
        return ExpenseStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to get stats: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)