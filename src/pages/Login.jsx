import { useState } from 'react';
import { supabase } from '../supabaseClient';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isSignUp, setIsSignUp] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    if (isSignUp) {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: { data: { name } }
      });
      if (error) setError(error.message);
      else setMessage('Account created! You can now sign in.');
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) setError(error.message);
    }
    setLoading(false);
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.logo}>✈️</div>
        <h1 style={styles.title}>TripMate</h1>
        <p style={styles.subtitle}>Plan trips together, stress less</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          {isSignUp && (
            <input
              style={styles.input}
              type="text"
              placeholder="Your name"
              value={name}
              onChange={e => setName(e.target.value)}
              required
            />
          )}
          <input
            style={styles.input}
            type="email"
            placeholder="Email address"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          {error && <div style={styles.error}>{error}</div>}
          {message && <div style={styles.success}>{message}</div>}
          <button style={styles.btn} type="submit" disabled={loading}>
            {loading ? '...' : isSignUp ? 'Create account →' : 'Sign in →'}
          </button>
        </form>

        <p style={styles.switch}>
          {isSignUp ? 'Already have an account? ' : "Don't have an account? "}
          <span style={styles.switchLink} onClick={() => { setIsSignUp(!isSignUp); setError(''); setMessage(''); }}>
            {isSignUp ? 'Sign in' : 'Sign up'}
          </span>
        </p>
      </div>
    </div>
  );
}

const styles = {
  container: { minHeight:'100vh', display:'flex', alignItems:'center', justifyContent:'center', background:'#f0f4f8', padding:'24px' },
  card: { width:'100%', maxWidth:'400px', background:'#fff', borderRadius:'24px', padding:'36px 28px', boxShadow:'0 4px 24px rgba(0,0,0,0.08)', display:'flex', flexDirection:'column', alignItems:'center' },
  logo: { fontSize:'52px', marginBottom:'8px' },
  title: { fontSize:'28px', fontWeight:'700', color:'#1a1a2e', letterSpacing:'-0.5px', margin:'0 0 4px' },
  subtitle: { fontSize:'15px', color:'#888', marginBottom:'28px', textAlign:'center' },
  form: { width:'100%', display:'flex', flexDirection:'column', gap:'12px' },
  input: { width:'100%', padding:'14px 16px', border:'1.5px solid #e2e8f0', borderRadius:'12px', fontSize:'15px', color:'#1a1a2e', outline:'none' },
  btn: { width:'100%', padding:'14px', background:'#378ADD', color:'#fff', border:'none', borderRadius:'12px', fontSize:'16px', fontWeight:'600', cursor:'pointer' },
  error: { background:'#FEF2F2', color:'#991B1B', padding:'10px 14px', borderRadius:'10px', fontSize:'13px' },
  success: { background:'#F0FDF4', color:'#166534', padding:'10px 14px', borderRadius:'10px', fontSize:'13px' },
  switch: { fontSize:'13px', color:'#666', marginTop:'16px' },
  switchLink: { color:'#378ADD', fontWeight:'600', cursor:'pointer' },
};