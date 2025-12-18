// components/auth/RegisterForm.tsx
'use client';

import { useState } from 'react';
import { registerUser } from '@/lib/api';
import AuthLayout from './AuthLayout';
import { useRouter } from 'next/navigation';
import { UserRole } from '@/types/users';

export default function RegisterForm() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [rol, setRol] = useState<UserRole>('cliente'); 
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!nombre.trim() || !email.trim()) {
      setError('Nombre y email son obligatorios');
      return;
    }

    setLoading(true);
    try {
      await registerUser(nombre, email, rol); // Llama a la API para insertar en la BD
      alert('Registro exitoso. ¡Inicia sesión con tu nuevo email!');
      router.push('/api/login');
    } catch (err: any) {
      setError(err.message || 'Error desconocido al registrar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="✍️ Registrar Usuario"
      footerText="¿Ya tienes cuenta?"
      footerLink="Inicia Sesión"
      footerHref="/login"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded-lg text-sm">
            {error}
          </div>
        )}
        <div>
          <label className="block text-sm text-slate-600 mb-1">Nombre</label>
          <input
            type="text"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-300"
            placeholder="Tu nombre completo"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-300"
            placeholder="tu.email@ejemplo.com"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-slate-600 mb-1">Rol</label>
          <select
            value={rol}
            onChange={(e) => setRol(e.target.value as UserRole)}
            className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-300"
          >
            <option value="cliente">Cliente</option>
            <option value="operador">Operador</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          // Color principal: bg-indigo-600
          className="w-full px-4 py-2 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition disabled:opacity-50 font-semibold"
        >
          {loading ? 'Registrando...' : 'Registrar'}
        </button>
      </form>
    </AuthLayout>
  );
}