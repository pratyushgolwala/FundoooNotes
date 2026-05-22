import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Login from '../components/Auth/Login';
import Signup from '../components/Auth/Signup';
import '../styles/auth.css';
import { FaCheckCircle } from 'react-icons/fa';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [emailVerified, setEmailVerified] = useState(false);
  const navigate = useNavigate();

  const handleAuthSuccess = () => {
    if (isLogin) {
      // Successful login - redirect to dashboard
      navigate('/dashboard');
    } else {
      // Successful signup - show message then switch to login
      setEmailVerified(true);
      setTimeout(() => {
        setIsLogin(true);
        setEmailVerified(false);
      }, 2000);
    }
  };

  return (
    <div className="auth-page">
      {emailVerified && (
        <div className="auth-message">
          <FaCheckCircle /> Email verified! You can now login.
        </div>
      )}

      {isLogin ? (
        <>
          <Login onSuccess={handleAuthSuccess} />
          <div className="auth-toggle">
            <p>Don't have an account?</p>
            <button onClick={() => setIsLogin(false)} className="toggle-btn">
              Sign Up
            </button>
          </div>
        </>
      ) : (
        <>
          <Signup onSuccess={handleAuthSuccess} />
          <div className="auth-toggle">
            <p>Already have an account?</p>
            <button onClick={() => setIsLogin(true)} className="toggle-btn">
              Sign In
            </button>
          </div>
        </>
      )}
    </div>
  );
}