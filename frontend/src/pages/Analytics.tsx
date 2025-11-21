import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, DollarSign, Download, Calendar, BarChart3, Zap, AlertCircle, Lightbulb, TrendingDown } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { getExpenses, getExpenseStats } from '../api/expenseApi';
import { getSpendingForecast, getCategoryForecast, getAnomalies, getTrends } from '../api/forecastApi';

export default function Analytics() {
  const userId = localStorage.getItem('expense_user') ? JSON.parse(localStorage.getItem('expense_user')!).id || '1' : '1';
  
  const [expenses, setExpenses] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [dailyData, setDailyData] = useState<any[]>([]);
  const [monthlyTrend, setMonthlyTrend] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // New prediction states
  const [forecast, setForecast] = useState<any>(null);
  const [categoryForecast, setCategoryForecast] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [insights, setInsights] = useState<any[]>([]);
  const [forecastDays, setForecastDays] = useState(30);

  const COLORS = ['#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#84cc16'];

  useEffect(() => {
    loadAnalyticsData();
    loadPredictions();
  }, [forecastDays]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [expensesData, statsData] = await Promise.all([
        getExpenses(userId),
        getExpenseStats(userId)
      ]);

      setExpenses(expensesData);
      setStats(statsData);

      // Process category data for pie chart
      if (statsData.by_category) {
        const catData = Object.entries(statsData.by_category).map(([name, value]) => ({
          name,
          value: value as number
        }));
        setCategoryData(catData);
      }

      // Process daily spending for last 7 days
      const last7Days = getLast7DaysData(expensesData);
      setDailyData(last7Days);

      // Process monthly trend for last 6 months
      const last6Months = getLast6MonthsData(expensesData);
      setMonthlyTrend(last6Months);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPredictions = async () => {
    try {
      const [forecastData, catForecastData, anomalyData, trendData] = await Promise.all([
        getSpendingForecast(userId, forecastDays).catch(() => null),
        getCategoryForecast(userId, forecastDays).catch(() => null),
        getAnomalies(userId).catch(() => null),
        getTrends(userId).catch(() => null)
      ]);

      if (forecastData?.success) {
        setForecast(forecastData);
      }
      if (catForecastData?.success) {
        setCategoryForecast(catForecastData);
      }
      if (anomalyData?.success) {
        setAnomalies(anomalyData.anomalies || []);
      }
      if (trendData?.success) {
        setInsights(trendData.insights || []);
      }
    } catch (error) {
      console.error('Failed to load predictions:', error);
    }
  };

  const getLast7DaysData = (expenses: any[]) => {
    const days = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      
      const dayExpenses = expenses.filter(exp => exp.date === dateStr);
      const total = dayExpenses.reduce((sum, exp) => sum + exp.amount, 0);
      
      days.push({
        date: date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
        amount: total
      });
    }
    return days;
  };

  const getLast6MonthsData = (expenses: any[]) => {
    const months = [];
    for (let i = 5; i >= 0; i--) {
      const date = new Date();
      date.setMonth(date.getMonth() - i);
      const monthStr = date.toISOString().slice(0, 7);
      
      const monthExpenses = expenses.filter(exp => exp.date.startsWith(monthStr));
      const total = monthExpenses.reduce((sum, exp) => sum + exp.amount, 0);
      
      months.push({
        month: date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
        amount: total
      });
    }
    return months;
  };

  const exportToCSV = () => {
    if (expenses.length === 0) {
      alert('No expenses to export');
      return;
    }

    const headers = ['Date', 'Category', 'Amount', 'Description'];
    const csvData = expenses.map(exp => [
      exp.date,
      exp.category,
      exp.amount,
      exp.description || ''
    ]);

    const csvContent = [
      headers.join(','),
      ...csvData.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `expenses_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
        <Sidebar />
        <main className="flex-1 lg:ml-64 p-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-violet-600 mx-auto"></div>
            <p className="mt-4 text-slate-600 font-medium">Loading analytics...</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Sidebar />
      
      <main className="flex-1 lg:ml-64 p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-blue-500 to-cyan-500 p-3.5 rounded-2xl shadow-lg shadow-blue-500/30">
                <BarChart3 className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                  Analytics & Reports
                </h1>
                <p className="text-slate-600 mt-1">Visualize your spending patterns</p>
              </div>
            </div>
            <button
              onClick={exportToCSV}
              className="px-6 py-3.5 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-semibold rounded-xl hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/30 flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              Export CSV
            </button>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-2xl p-6 shadow-xl border border-slate-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-violet-100 p-2 rounded-lg">
                  <DollarSign className="w-5 h-5 text-violet-600" />
                </div>
                <p className="text-sm font-medium text-slate-600">Total Expenses</p>
              </div>
              <p className="text-3xl font-bold text-slate-900">₹{(stats?.month || 0).toFixed(2)}</p>
              <p className="text-xs text-slate-500 mt-1">This month</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-xl border border-slate-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                </div>
                <p className="text-sm font-medium text-slate-600">Daily Average</p>
              </div>
              <p className="text-3xl font-bold text-slate-900">₹{((stats?.month || 0) / 30).toFixed(2)}</p>
              <p className="text-xs text-slate-500 mt-1">Per day</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-xl border border-slate-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-emerald-100 p-2 rounded-lg">
                  <Calendar className="w-5 h-5 text-emerald-600" />
                </div>
                <p className="text-sm font-medium text-slate-600">This Week</p>
              </div>
              <p className="text-3xl font-bold text-slate-900">₹{(stats?.week || 0).toFixed(2)}</p>
              <p className="text-xs text-slate-500 mt-1">Last 7 days</p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-xl border border-slate-200">
              <div className="flex items-center gap-3 mb-2">
                <div className="bg-orange-100 p-2 rounded-lg">
                  <DollarSign className="w-5 h-5 text-orange-600" />
                </div>
                <p className="text-sm font-medium text-slate-600">Largest</p>
              </div>
              <p className="text-3xl font-bold text-slate-900">₹{(stats?.largest || 0).toFixed(2)}</p>
              <p className="text-xs text-slate-500 mt-1">Single expense</p>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Category Distribution - Pie Chart */}
            <div className="bg-white rounded-3xl p-8 shadow-2xl border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-6">Spending by Category</h3>
              {categoryData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={categoryData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {categoryData.map((_entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => `₹${value.toFixed(2)}`} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-slate-500">
                  No data available
                </div>
              )}
            </div>

            {/* Last 7 Days - Bar Chart */}
            <div className="bg-white rounded-3xl p-8 shadow-2xl border border-slate-200">
              <h3 className="text-xl font-bold text-slate-900 mb-6">Last 7 Days</h3>
              {dailyData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(value: any) => `₹${value.toFixed(2)}`} />
                    <Bar dataKey="amount" fill="url(#colorGradient)" radius={[8, 8, 0, 0]} />
                    <defs>
                      <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#8b5cf6" />
                        <stop offset="100%" stopColor="#a78bfa" />
                      </linearGradient>
                    </defs>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-slate-500">
                  No data available
                </div>
              )}
            </div>
          </div>

          {/* Monthly Trend - Line Chart */}
          <div className="bg-white rounded-3xl p-8 shadow-2xl border border-slate-200 mb-8">
            <h3 className="text-xl font-bold text-slate-900 mb-6">6-Month Trend</h3>
            {monthlyTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={monthlyTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value: any) => `₹${value.toFixed(2)}`} />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="amount" 
                    stroke="#8b5cf6" 
                    strokeWidth={3}
                    dot={{ fill: '#8b5cf6', r: 6 }}
                    activeDot={{ r: 8 }}
                    name="Spending"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[350px] flex items-center justify-center text-slate-500">
                No data available
              </div>
            )}
          </div>

          {/* Prophet AI Predictions Section */}
          {forecast && forecast.success && (
            <div className="bg-gradient-to-br from-violet-50 to-purple-50 rounded-3xl p-8 shadow-2xl border-2 border-violet-200 mb-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="bg-gradient-to-br from-violet-600 to-purple-600 p-2.5 rounded-xl">
                    <Zap className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-slate-900">Prophet AI Forecast</h3>
                    <p className="text-slate-600">Next {forecastDays} days spending prediction</p>
                  </div>
                </div>
                <select
                  value={forecastDays}
                  onChange={(e) => setForecastDays(Number(e.target.value))}
                  className="px-4 py-2 bg-white border-2 border-violet-200 rounded-xl font-medium text-slate-700 focus:outline-none focus:border-violet-500"
                >
                  <option value={7}>7 Days</option>
                  <option value={14}>14 Days</option>
                  <option value={30}>30 Days</option>
                  <option value={60}>60 Days</option>
                </select>
              </div>

              {/* Forecast Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="bg-white rounded-2xl p-6 shadow-lg border border-violet-200">
                  <p className="text-sm font-medium text-slate-600 mb-2">Predicted Total</p>
                  <p className="text-3xl font-bold text-violet-600">₹{forecast.summary.total_predicted.toFixed(2)}</p>
                  <p className="text-xs text-slate-500 mt-1">For next {forecastDays} days</p>
                </div>
                <div className="bg-white rounded-2xl p-6 shadow-lg border border-violet-200">
                  <p className="text-sm font-medium text-slate-600 mb-2">Daily Average</p>
                  <p className="text-3xl font-bold text-purple-600">₹{forecast.summary.daily_average.toFixed(2)}</p>
                  <p className="text-xs text-slate-500 mt-1">Expected per day</p>
                </div>
                <div className="bg-white rounded-2xl p-6 shadow-lg border border-violet-200">
                  <p className="text-sm font-medium text-slate-600 mb-2">Confidence</p>
                  <p className="text-3xl font-bold text-emerald-600 capitalize">{forecast.summary.confidence}</p>
                  <p className="text-xs text-slate-500 mt-1">Prediction accuracy</p>
                </div>
              </div>

              {/* Forecast Chart */}
              <div className="bg-white rounded-2xl p-6 shadow-lg">
                <h4 className="text-lg font-bold text-slate-900 mb-4">Daily Forecast with Confidence Interval</h4>
                <ResponsiveContainer width="100%" height={350}>
                  <AreaChart data={forecast.forecast}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip formatter={(value: any) => `₹${value.toFixed(2)}`} />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="upper" 
                      stackId="1"
                      stroke="#c4b5fd" 
                      fill="#c4b5fd" 
                      fillOpacity={0.3}
                      name="Upper Bound"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="predicted" 
                      stackId="2"
                      stroke="#8b5cf6" 
                      fill="#8b5cf6" 
                      strokeWidth={3}
                      name="Predicted"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="lower" 
                      stackId="1"
                      stroke="#ddd6fe" 
                      fill="#ddd6fe" 
                      fillOpacity={0.3}
                      name="Lower Bound"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Category Forecasts */}
          {categoryForecast && categoryForecast.success && Object.keys(categoryForecast.forecasts).length > 0 && (
            <div className="bg-white rounded-3xl p-8 shadow-2xl border border-slate-200 mb-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-gradient-to-br from-blue-500 to-cyan-500 p-2.5 rounded-xl">
                  <TrendingUp className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900">Category Predictions</h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Object.entries(categoryForecast.forecasts).map(([category, data]: [string, any]) => (
                  <div key={category} className="bg-gradient-to-br from-slate-50 to-white rounded-2xl p-6 border border-slate-200 hover:shadow-lg transition-shadow">
                    <h4 className="text-lg font-bold text-slate-900 mb-3">{category}</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-600">Predicted:</span>
                        <span className="font-bold text-slate-900">₹{data.predicted_total.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-600">Daily Avg:</span>
                        <span className="font-semibold text-slate-700">₹{data.daily_average.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center gap-2 pt-2">
                        {data.trend === 'increasing' ? (
                          <TrendingUp className="w-4 h-4 text-red-500" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-green-500" />
                        )}
                        <span className={`text-sm font-medium ${data.trend === 'increasing' ? 'text-red-600' : 'text-green-600'}`}>
                          {data.trend}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Smart Insights */}
          {insights.length > 0 && (
            <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-3xl p-8 shadow-2xl border-2 border-amber-200 mb-8">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="bg-gradient-to-br from-amber-500 to-orange-500 p-2.5 rounded-xl">
                    <Lightbulb className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-slate-900">Smart Insights & Recommendations</h3>
                </div>
                {insights[0] && insights.length > 0 && (
                  <div className="text-right">
                    <p className="text-xs text-slate-600 mb-1">Potential Monthly Savings</p>
                    <p className="text-2xl font-bold text-emerald-600">
                      ₹{insights.reduce((sum: number, i: any) => sum + (i.savings_potential || 0), 0).toFixed(2)}
                    </p>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {insights.map((insight, index) => (
                  <div key={index} className="bg-white rounded-2xl p-6 border border-amber-200 hover:shadow-lg transition-shadow">
                    <div className="flex items-start justify-between mb-3">
                      <h4 className="text-lg font-bold text-slate-900 flex-1">{insight.message}</h4>
                      {insight.savings_potential && insight.savings_potential > 0 && (
                        <div className="ml-3 px-3 py-1 bg-emerald-100 text-emerald-700 text-sm font-bold rounded-lg whitespace-nowrap">
                          Save ₹{insight.savings_potential.toFixed(0)}
                        </div>
                      )}
                    </div>
                    <p className="text-slate-600 text-sm leading-relaxed mb-3">{insight.tip}</p>
                    <div className="flex items-center justify-between">
                      <div className="px-3 py-1 bg-amber-100 text-amber-700 text-xs font-medium rounded-lg">
                        {insight.type.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Anomalies Detection */}
          {anomalies.length > 0 && (
            <div className="bg-gradient-to-br from-red-50 to-pink-50 rounded-3xl p-8 shadow-2xl border-2 border-red-200 mb-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-gradient-to-br from-red-500 to-pink-500 p-2.5 rounded-xl">
                  <AlertCircle className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-slate-900">Unusual Spending Detected</h3>
              </div>

              <div className="space-y-4">
                {anomalies.map((anomaly, index) => (
                  <div key={index} className={`bg-white rounded-2xl p-6 border-2 ${anomaly.severity === 'high' ? 'border-red-300' : 'border-orange-300'} hover:shadow-lg transition-shadow`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-lg font-bold text-slate-900">₹{anomaly.amount.toFixed(2)}</p>
                        <p className="text-sm text-slate-600">{anomaly.date}</p>
                      </div>
                      <div className="text-right">
                        <div className={`px-3 py-1 rounded-lg inline-block ${anomaly.severity === 'high' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'}`}>
                          <span className="text-sm font-bold">{anomaly.deviation > 0 ? '+' : ''}{anomaly.deviation}%</span>
                        </div>
                        <p className="text-xs text-slate-500 mt-1 capitalize">{anomaly.severity} severity</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
