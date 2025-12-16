// app/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { Ticket } from '@/types/ticket';
import { getTickets } from '@/lib/api';
import TicketCard from '@/components/TicketCard';
import DashboardStats from '@/components/DashboardStats';
import NewTicketModal from '@/components/NewTicketModal';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation'; // <-- AGREGAR ESTA IMPORTACIÓN

export default function Page() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [mostrarModal, setMostrarModal] = useState(false);
  const { user, role, loading, logout } = useAuth(); 
  const router = useRouter(); 

  /* =========================
     PROTECCIÓN DE RUTA
  ========================== */
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login'); // Redirige a login si no hay usuario
    }
  }, [loading, user, router]);

  /* =========================
     CARGAR TICKETS
  ========================== */
  const refrescarTickets = async () => {
    if (user) {
      const data = await getTickets();
      setTickets(data);
    }
  };

  useEffect(() => {
      if (user) {
          refrescarTickets();
      }
  }, [user]); 

  const actualizarTicket = async (updatedTicket: Ticket) => {
    // ... (El resto de esta función se mantiene igual)
  };

  // Bloquea el renderizado si no hay usuario o está cargando
  if (loading || !user) return null; 

  return (
    <main className="p-8 max-w-7xl mx-auto">

      {/* BOTÓN DE CERRAR SESIÓN */}
      <button
        onClick={logout}
        className="fixed top-4 right-4 px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition"
      >
        Cerrar Sesión ({user.rol})
      </button>

      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-slate-800">
          🎫 Gestión de Tickets (Usuario: {user.nombre})
        </h1>
        {/* Usando el color principal: bg-indigo-600 */}
        <button
          onClick={() => setMostrarModal(true)}
          className="px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition"
        >
          ➕ Nuevo Ticket
        </button>
      </div>
      
      {/* STATS */}
      <DashboardStats tickets={tickets} />

      {/* LISTA */}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {tickets.map((ticket) => (
          <TicketCard
            key={ticket.id}
            ticket={ticket}
            onUpdate={actualizarTicket}
          />
        ))}
      </section>

      {/* MODAL NUEVO TICKET */}
      {mostrarModal && (
        <NewTicketModal
          onClose={() => setMostrarModal(false)}
          onCreated={refrescarTickets} 
        />
      )}
    </main>
  );
}