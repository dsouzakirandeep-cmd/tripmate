import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { supabase } from './supabaseClient';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import TripDetail from './pages/TripDetail';

export default function App() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });
    return () => subscription.unsubscribe();
  }, []);

  if (loading) return (
    <div style={{display:'flex',alignItems:'center',justifyContent:'center',height:'100vh',fontSize:'32px'}}>
      ✈️
    </div>
  );

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={!session ? <Login /> : <Navigate to="/dashboard" />} />
        <Route path="/dashboard" element={session ? <Dashboard session={session} /> : <Navigate to="/" />} />
        <Route path="/trip/:id" element={session ? <TripDetail session={session} /> : <Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}