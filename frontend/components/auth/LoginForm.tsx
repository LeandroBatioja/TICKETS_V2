// components/auth/LoginForm.tsx
'use client';

import { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import AuthLayout from './AuthLayout';

export default function LoginForm() {
  const [email, setEmail] = useState(''); 
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim()) {
      setError('El email es obligatorio');
      return;
    }

    setLoading(true);
    try {
      await login(email); 
    } catch (err: any) {
      // Muestra el error del backend (ej: "Credenciales inválidas")
      setError(err.message || 'Error desconocido al iniciar sesión');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="🔑 Iniciar Sesión"
      footerText="¿No tienes cuenta?"
      footerLink="Regístrate"
      footerHref="/register"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}
        <div>
          <label className="block text-sm text-slate-600 mb-1">
            Email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-300"
            placeholder="Introduce tu email registrado"
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          // Color principal: bg-indigo-600
          className="w-full px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition disabled:opacity-50 font-semibold"
        >
          {loading ? 'Verificando...' : 'Iniciar Sesión'}
        </button>
      </form>
    </AuthLayout>
  );
}