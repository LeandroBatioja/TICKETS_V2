// components/NewTicketModal.tsx
'use client';

import { useState } from 'react';
import { crearTicket } from '@/lib/api';
import { useAuth } from '@/context/AuthContext'; // <-- ¡IMPORTANTE!

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export default function NewTicketModal({ onClose, onCreated }: Props) {
  const { user } = useAuth(); // <-- OBTENEMOS EL USUARIO LOGEADO
  const [asunto, setAsunto] = useState('');
  const [prioridad, setPrioridad] = useState<'baja' | 'media' | 'alta'>('baja');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Verificación crucial
    if (!user || !user.id) {
        setError("Error: No se pudo obtener el ID del usuario logeado.");
        return;
    }
    
    if (asunto.length < 5) {
        setError("El asunto debe tener al menos 5 caracteres.");
        return;
    }

    setLoading(true);
    try {
        // ENVIAMOS EL ID DEL USUARIO LOGEADO (user.id)
        await crearTicket({
            id_usuario: user.id, // <-- USANDO EL ID DEL CONTEXTO
            asunto,
            prioridad,
        });

        onCreated();
        onClose();
    } catch (err: any) {
        // Mostrar el error específico del backend
        setError(err.message || 'Error desconocido al crear el ticket');
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white p-6 rounded-lg shadow-2xl w-full max-w-md">
        <h2 className="text-2xl font-bold mb-4 text-slate-800">Crear Nuevo Ticket</h2>
        
        {error && (
          <div className="bg-red-100 text-red-700 p-3 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700">Asunto</label>
            <input
              type="text"
              value={asunto}
              onChange={(e) => setAsunto(e.target.value)}
              className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Descripción breve del problema"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">Prioridad</label>
            <select
              value={prioridad}
              onChange={(e) => setPrioridad(e.target.value as 'baja' | 'media' | 'alta')}
              className="mt-1 w-full border rounded-lg px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="baja">Baja</option>
              <option value="media">Media</option>
              <option value="alta">Alta</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-700 bg-slate-200 rounded-xl hover:bg-slate-300 transition"
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-xl hover:bg-indigo-700 transition disabled:opacity-50"
              disabled={loading}
            >
              {loading ? 'Creando...' : 'Crear Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}