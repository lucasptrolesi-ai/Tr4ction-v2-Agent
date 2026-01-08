'use client';

import { useState } from 'react';

export default function TestLogin() {
  const [email, setEmail] = useState('admin@tr4ction.com');
  const [password, setPassword] = useState('admin');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

  const handleLogin = async () => {
    setLoading(true);
    setResult('⏳ Tentando login...');

    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        setResult(`
          ✅ LOGIN BEM-SUCEDIDO!\n
          Usuário: ${data.user.name}\n
          Email: ${data.user.email}\n
          Papel: ${data.user.role}\n
          Token: ${data.access_token.substring(0, 30)}...
        `);
        localStorage.setItem('tr4ction_token', data.access_token);
      } else {
        setResult(`❌ Erro: ${data.detail}`);
      }
    } catch (error) {
      setResult(`❌ Erro de conexão: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '40px auto', padding: '20px', background: '#f5f5f5', borderRadius: '8px' }}>
      <h1>🔐 Test Login</h1>
      <input 
        type="email" 
        value={email} 
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
      />
      <input 
        type="password" 
        value={password} 
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Senha"
        style={{ width: '100%', padding: '10px', marginBottom: '10px' }}
      />
      <button 
        onClick={handleLogin}
        disabled={loading}
        style={{ width: '100%', padding: '10px', background: '#007bff', color: 'white', border: 'none', cursor: 'pointer' }}
      >
        {loading ? 'Tentando...' : 'Login'}
      </button>
      {result && (
        <pre style={{ marginTop: '20px', padding: '10px', background: '#e8f5e9', borderRadius: '4px', whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
          {result}
        </pre>
      )}
    </div>
  );
}
