// app/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { Ticket } from '@/types/ticket';
import { getTickets } from '@/lib/api';
import TicketCard from '@/components/TicketCard';
import DashboardStats from '@/components/DashboardStats';
import NewTicketModal from '@/components/NewTicketModal';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';

export default function Page() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [mostrarModal, setMostrarModal] = useState(false);
  const { user, role, loading, logout } = useAuth(); 
  const router = useRouter(); 

  /* =========================
     PROTECCIÓN Y CARGA
  ========================== */
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login'); 
    }
  }, [loading, user, router]);

  const refrescarTickets = async () => {
    if (user && role) {
      // Pasa el ID y el Rol al backend para filtrar la lista
      try {
        const data = await getTickets(user.id, role); 
        setTickets(data);
      } catch (error) {
          console.error("Fallo al cargar tickets:", error);
      }
    }
  };

  useEffect(() => {
      if (user) {
          refrescarTickets();
      }
  }, [user]); 

  const actualizarTicket = async (updatedTicket: Ticket) => {
    setTickets((prev) =>
      prev.map((t) => (t.id === updatedTicket.id ? updatedTicket : t))
    );
  };

  if (loading || !user) return null; 

  return (
    <main className="p-8 max-w-7xl mx-auto">

      {/* BOTÓN DE CERRAR SESIÓN */}
      <button
        onClick={logout}
        className="top-4 right-4 px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600 transition"
      >
        Cerrar Sesión ({user.rol})
      </button>

      {/* HEADER */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-slate-800">
          🎫 Gestión de Tickets (Rol: {role})
        </h1>
        
        {/* LÓGICA DE VISIBILIDAD: SOLO EL OPERADOR PUEDE CREAR TICKET */}
        {role === 'operador' && (
          <button
            onClick={() => setMostrarModal(true)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition"
          >
            ➕ Nuevo Ticket para Cliente
          </button>
        )}
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