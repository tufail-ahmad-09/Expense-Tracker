import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, DollarSign, Download, Calendar, BarChart3 } from 'lucide-react';
import Sidebar from '../components/Sidebar';
import { getExpenses, getExpenseStats } from '../api/expenseApi';

export default function Analytics() {
  const userId = localStorage.getItem('expense_user') ? JSON.parse(localStorage.getItem('expense_user')!).id || '1' : '1';
  
  const [expenses, setExpenses] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [dailyData, setDailyData] = useState<any[]>([]);
  const [monthlyTrend, setMonthlyTrend] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const COLORS = ['#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#84cc16'];

  useEffect(() => {
    loadAnalyticsData();
  }, []);

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
          <div className="bg-white rounded-3xl p-8 shadow-2xl border border-slate-200">
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
        </div>
      </main>
    </div>
  );
}
