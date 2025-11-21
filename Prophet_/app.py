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

@app.get("/api/forecast/spending/{user_id}")
async def forecast_spending(user_id: str, days: int = 30):
    """
    Forecast future spending using Prophet ML
    """
    try:
        # Get historical expenses
        expenses = get_user_expenses(int(user_id))
        
        if len(expenses) < 7:
            return {
                "success": False,
                "message": "Need at least 7 days of expense data for accurate predictions",
                "forecast": []
            }
        
        # Prepare data for Prophet
        df = pd.DataFrame(expenses)
        df['date'] = pd.to_datetime(df['date'])
        
        # Aggregate by date
        daily_spending = df.groupby('date')['amount'].sum().reset_index()
        daily_spending.columns = ['ds', 'y']
        
        # Fill missing dates with 0
        date_range = pd.date_range(start=daily_spending['ds'].min(), end=daily_spending['ds'].max())
        daily_spending = daily_spending.set_index('ds').reindex(date_range, fill_value=0).reset_index()
        daily_spending.columns = ['ds', 'y']
        
        # Train Prophet model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05
        )
        model.fit(daily_spending)
        
        # Make future predictions
        future = model.make_future_dataframe(periods=days)
        forecast = model.predict(future)
        
        # Get only future predictions
        future_forecast = forecast.tail(days)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
        future_forecast['yhat'] = future_forecast['yhat'].clip(lower=0)
        future_forecast['yhat_lower'] = future_forecast['yhat_lower'].clip(lower=0)
        future_forecast['yhat_upper'] = future_forecast['yhat_upper'].clip(lower=0)
        
        forecast_data = [
            {
                'date': row['ds'].strftime('%Y-%m-%d'),
                'predicted': round(row['yhat'], 2),
                'lower': round(row['yhat_lower'], 2),
                'upper': round(row['yhat_upper'], 2)
            }
            for _, row in future_forecast.iterrows()
        ]
        
        # Calculate summary statistics
        total_predicted = round(future_forecast['yhat'].sum(), 2)
        daily_average = round(future_forecast['yhat'].mean(), 2)
        
        return {
            "success": True,
            "forecast": forecast_data,
            "summary": {
                "total_predicted": total_predicted,
                "daily_average": daily_average,
                "period_days": days,
                "confidence": "medium" if len(expenses) < 30 else "high"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to generate forecast: {str(e)}"}
        )

@app.get("/api/forecast/category/{user_id}")
async def forecast_by_category(user_id: str, days: int = 30):
    """
    Forecast spending by category using Prophet ML
    """
    try:
        # Get historical expenses
        expenses = get_user_expenses(int(user_id))
        
        if len(expenses) < 7:
            return {
                "success": False,
                "message": "Need at least 7 days of expense data for accurate predictions",
                "forecasts": {}
            }
        
        df = pd.DataFrame(expenses)
        df['date'] = pd.to_datetime(df['date'])
        
        categories = df['category'].unique()
        category_forecasts = {}
        
        for category in categories:
            category_data = df[df['category'] == category]
            
            if len(category_data) < 3:
                continue
            
            # Aggregate by date for this category
            daily_spending = category_data.groupby('date')['amount'].sum().reset_index()
            daily_spending.columns = ['ds', 'y']
            
            # Fill missing dates with 0
            date_range = pd.date_range(start=daily_spending['ds'].min(), end=daily_spending['ds'].max())
            daily_spending = daily_spending.set_index('ds').reindex(date_range, fill_value=0).reset_index()
            daily_spending.columns = ['ds', 'y']
            
            try:
                # Train Prophet model
                model = Prophet(
                    daily_seasonality=False,
                    weekly_seasonality=True,
                    yearly_seasonality=False,
                    changepoint_prior_scale=0.05
                )
                model.fit(daily_spending)
                
                # Make predictions
                future = model.make_future_dataframe(periods=days)
                forecast = model.predict(future)
                
                # Calculate prediction
                future_forecast = forecast.tail(days)['yhat'].clip(lower=0)
                total_predicted = round(future_forecast.sum(), 2)
                
                category_forecasts[category] = {
                    'predicted_total': total_predicted,
                    'daily_average': round(future_forecast.mean(), 2),
                    'trend': 'increasing' if forecast['trend'].iloc[-1] > forecast['trend'].iloc[-days] else 'decreasing'
                }
            except Exception as e:
                print(f"Error forecasting {category}: {str(e)}")
                continue
        
        return {
            "success": True,
            "forecasts": category_forecasts,
            "period_days": days
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to generate category forecasts: {str(e)}"}
        )

@app.get("/api/insights/anomalies/{user_id}")
async def detect_anomalies(user_id: str):
    """
    Detect unusual spending patterns
    """
    try:
        expenses = get_user_expenses(int(user_id))
        
        if len(expenses) < 7:
            return {
                "success": False,
                "message": "Need more data to detect anomalies",
                "anomalies": []
            }
        
        df = pd.DataFrame(expenses)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate daily spending
        daily_spending = df.groupby('date')['amount'].sum().reset_index()
        
        # Calculate statistics
        mean_spending = daily_spending['amount'].mean()
        std_spending = daily_spending['amount'].std()
        threshold = mean_spending + (2 * std_spending)
        
        # Find anomalies
        anomalies = daily_spending[daily_spending['amount'] > threshold]
        
        anomaly_data = [
            {
                'date': row['date'].strftime('%Y-%m-%d'),
                'amount': round(row['amount'], 2),
                'deviation': round(((row['amount'] - mean_spending) / mean_spending) * 100, 1),
                'severity': 'high' if row['amount'] > (mean_spending + 3 * std_spending) else 'medium'
            }
            for _, row in anomalies.iterrows()
        ]
        
        return {
            "success": True,
            "anomalies": anomaly_data,
            "baseline": {
                "average_daily": round(mean_spending, 2),
                "threshold": round(threshold, 2)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to detect anomalies: {str(e)}"}
        )

@app.get("/api/insights/trends/{user_id}")
async def analyze_trends(user_id: str):
    """
    Analyze spending trends and patterns with AI-powered recommendations
    """
    try:
        expenses = get_user_expenses(int(user_id))
        
        if len(expenses) < 14:
            return {
                "success": False,
                "message": "Need at least 2 weeks of data for trend analysis",
                "insights": []
            }
        
        df = pd.DataFrame(expenses)
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.day_name()
        df['is_weekend'] = df['date'].dt.dayofweek >= 5
        
        insights = []
        
        # 1. Weekend vs Weekday Analysis
        weekend_spending = df[df['is_weekend']]['amount'].sum()
        weekday_spending = df[~df['is_weekend']]['amount'].sum()
        weekend_days = df[df['is_weekend']]['date'].nunique()
        weekday_days = df[~df['is_weekend']]['date'].nunique()
        
        if weekend_days > 0 and weekday_days > 0:
            weekend_avg = weekend_spending / weekend_days
            weekday_avg = weekday_spending / weekday_days
            
            if weekend_avg > weekday_avg * 1.3:
                diff_percent = round(((weekend_avg - weekday_avg) / weekday_avg) * 100)
                insights.append({
                    'type': 'weekend_pattern',
                    'message': f'You spend {diff_percent}% more on weekends (₹{round(weekend_avg, 2)}/day vs ₹{round(weekday_avg, 2)}/day)',
                    'tip': 'Try planning weekend activities with a fixed budget. Meal prep on Sundays to reduce weekend food costs.',
                    'savings_potential': round((weekend_avg - weekday_avg) * 8, 2)  # 8 weekend days per month
                })
        
        # 2. Day of week analysis with best shopping day
        dow_spending = df.groupby('day_of_week')['amount'].mean().to_dict()
        max_day = max(dow_spending, key=dow_spending.get)
        min_day = min(dow_spending, key=dow_spending.get)
        
        if dow_spending[max_day] > dow_spending[min_day] * 1.5:
            insights.append({
                'type': 'best_shopping_day',
                'message': f'{min_day}s are your most frugal days (₹{round(dow_spending[min_day], 2)} avg)',
                'tip': f'Schedule major purchases for {min_day}s when you naturally spend less. Avoid shopping on {max_day}s.',
                'savings_potential': round((dow_spending[max_day] - dow_spending[min_day]) * 4, 2)
            })
        
        # 3. Category-specific optimization
        category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
        total = category_spending.sum()
        
        # Find overspending categories
        for category, amount in category_spending.head(3).items():
            percentage = (amount / total) * 100
            category_count = len(df[df['category'] == category])
            avg_per_transaction = amount / category_count
            
            if percentage > 35:
                insights.append({
                    'type': 'category_optimization',
                    'message': f'{category}: {round(percentage)}% of budget (₹{round(amount, 2)})',
                    'tip': f'Consider these alternatives: 1) Set a weekly limit of ₹{round(amount/4, 2)} 2) Find cheaper alternatives 3) Reduce frequency by 20%',
                    'savings_potential': round(amount * 0.15, 2)  # 15% potential savings
                })
        
        # 4. Spending momentum with predictive alert
        recent_week = df[df['date'] >= df['date'].max() - pd.Timedelta(days=7)]['amount'].sum()
        previous_week = df[(df['date'] >= df['date'].max() - pd.Timedelta(days=14)) & 
                          (df['date'] < df['date'].max() - pd.Timedelta(days=7))]['amount'].sum()
        
        if previous_week > 0:
            change = ((recent_week - previous_week) / previous_week) * 100
            if abs(change) > 20:
                if change > 0:
                    projected_monthly = recent_week * 4.33
                    insights.append({
                        'type': 'momentum_alert',
                        'message': f'⚠️ Spending increased {abs(round(change))}% this week (₹{round(recent_week, 2)})',
                        'tip': f'At this rate, you\'ll spend ₹{round(projected_monthly, 2)} this month. Review discretionary expenses immediately.',
                        'savings_potential': round(recent_week - previous_week, 2)
                    })
                else:
                    insights.append({
                        'type': 'momentum_success',
                        'message': f'✨ Excellent! Spending decreased {abs(round(change))}% this week',
                        'tip': 'Keep up the great work! Consider moving these savings to your emergency fund.',
                        'savings_potential': round(previous_week - recent_week, 2)
                    })
        
        # 5. Smart savings recommendations
        avg_transaction = df['amount'].mean()
        large_transactions = df[df['amount'] > avg_transaction * 3]
        
        if len(large_transactions) > 0:
            large_total = large_transactions['amount'].sum()
            insights.append({
                'type': 'large_purchase_review',
                'message': f'{len(large_transactions)} large purchase(s) totaling ₹{round(large_total, 2)}',
                'tip': 'For purchases over ₹' + str(round(avg_transaction * 2, 2)) + ', wait 24 hours before buying. This reduces impulse spending by 30%.',
                'savings_potential': round(large_total * 0.2, 2)
            })
        
        # 6. Category reallocation suggestion
        if len(category_spending) >= 3:
            top_3_total = category_spending.head(3).sum()
            bottom_categories = category_spending[3:]
            
            if top_3_total > total * 0.75:
                insights.append({
                    'type': 'budget_reallocation',
                    'message': f'Top 3 categories consume {round((top_3_total/total)*100)}% of your budget',
                    'tip': f'Consider reallocating 10% from {category_spending.index[0]} (₹{round(category_spending.iloc[0] * 0.1, 2)}) to emergency savings or debt reduction.',
                    'savings_potential': round(category_spending.iloc[0] * 0.1, 2)
                })
        
        # 7. Frequency-based insight
        daily_expenses = df.groupby(df['date'].dt.date).size()
        high_frequency_days = len(daily_expenses[daily_expenses >= 5])
        
        if high_frequency_days > 0:
            insights.append({
                'type': 'transaction_frequency',
                'message': f'{high_frequency_days} days with 5+ transactions',
                'tip': 'Multiple small purchases add up! Try the "cash envelope" method or set a daily transaction limit.',
                'savings_potential': round(avg_transaction * high_frequency_days * 0.5, 2)
            })
        
        # Calculate total potential savings
        total_savings_potential = sum(insight.get('savings_potential', 0) for insight in insights)
        
        return {
            "success": True,
            "insights": insights,
            "statistics": {
                'total_expenses': len(expenses),
                'average_transaction': round(avg_transaction, 2),
                'days_tracked': (df['date'].max() - df['date'].min()).days + 1,
                'total_savings_potential': round(total_savings_potential, 2)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": f"Failed to analyze trends: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)