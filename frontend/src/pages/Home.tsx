/**
 * Home/Landing Page
 * Public page with links to Signup/Signin
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Lock, Zap } from 'lucide-react';

export const Home: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 text-blue-600 mr-2" />
            <h1 className="text-2xl font-bold text-gray-800">Expense Tracker</h1>
          </div>
          <div className="flex gap-4">
            <Link
              to="/signin"
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 focus:outline-none focus:underline"
            >
              Sign In
            </Link>
            <Link
              to="/signup"
              className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-grow container mx-auto px-4 py-16 flex items-center">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Track Your Expenses.<br />
            <span className="text-blue-600">Predict Your Future.</span>
          </h2>
          <p className="text-xl text-gray-700 mb-12 max-w-2xl mx-auto">
            Advanced machine learning forecasting for your financial data. 
            Upload your expense history and get accurate predictions powered by Prophet.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Link
              to="/signup"
              className="px-8 py-4 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all shadow-lg hover:shadow-xl"
            >
              Create Free Account
            </Link>
            <Link
              to="/signin"
              className="px-8 py-4 text-lg font-medium text-blue-600 bg-white rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-all shadow-lg hover:shadow-xl"
            >
              Sign In
            </Link>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mt-16">
            <div className="bg-white rounded-lg p-6 shadow-md">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                Accurate Forecasting
              </h3>
              <p className="text-gray-600">
                Leverage Prophet's time series forecasting to predict future expenses with high accuracy.
              </p>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-md">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Lock className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                Secure & Private
              </h3>
              <p className="text-gray-600">
                Your financial data is encrypted and secure. We never share your information.
              </p>
            </div>

            <div className="bg-white rounded-lg p-6 shadow-md">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                Fast & Easy
              </h3>
              <p className="text-gray-600">
                Upload your CSV, get predictions in seconds. Simple interface, powerful results.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-6">
        <div className="container mx-auto px-4 text-center text-gray-600 text-sm">
          <p>© 2025 Expense Tracker. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};
