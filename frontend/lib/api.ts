// lib/api.ts
import { Ticket } from '@/types/ticket';
import { User, UserRole } from '@/types/users'; 

const API_URL = 'http://127.0.0.1:8000';

/* ======================================================
   AUTENTICACIÓN (100% BD)
====================================================== */

export async function getUsuarioActual(): Promise<User> {
  const res = await fetch(`${API_URL}/me`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error('No autenticado'); 
  }

  return res.json();
}

export async function loginUser(email: string): Promise<User> {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    // Envía el email a FastAPI para que lo busque en la BD
    body: JSON.stringify({ email: email }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Error desconocido al iniciar sesión');
  }

  return res.json();
}

export async function registerUser(nombre: string, email: string, rol: UserRole) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    // Envía los datos a FastAPI para que los inserte en la BD
    body: JSON.stringify({
      nombre: nombre,
      email: email,
      rol: rol, 
    }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || 'Error al registrar usuario');
  }

  return res.json();
}


/* ================= MAPPER Y API TICKETS (CÓDIGO EXISTENTE) ================= */
interface TicketBackend {
  id_ticket: number;
  asunto: string;
  prioridad: 'baja' | 'media' | 'alta';
  estado: 'abierto' | 'en_proceso' | 'cerrado';
  fecha_creacion: string;
}

function mapTicket(t: TicketBackend): Ticket {
  return {
    id: String(t.id_ticket),
    asunto: t.asunto,
    descripcion: '',
    prioridad:
      t.prioridad.charAt(0).toUpperCase() +
      t.prioridad.slice(1) as Ticket['prioridad'],

    estado:
      t.estado === 'en_proceso'
        ? 'En Progreso'
        : t.estado.charAt(0).toUpperCase() +
          t.estado.slice(1) as Ticket['estado'],

    fechaCreacion: new Date(t.fecha_creacion),
  };
}

export async function getTickets(): Promise<Ticket[]> {
  const res = await fetch(`${API_URL}/tickets`, {
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error('Error al obtener tickets');
  }

  const data: TicketBackend[] = await res.json();
  return data.map(mapTicket);
}

// VERIFICAR ESTA FUNCIÓN:
export async function crearTicket(data: {
  id_usuario: number;
  asunto: string;
  prioridad: 'baja' | 'media' | 'alta';
}) {
  // Asegurarse que los parámetros se envíen como Query Params (como espera FastAPI)
  const params = new URLSearchParams({
    id_usuario: String(data.id_usuario),
    asunto: data.asunto,
    prioridad: data.prioridad,
  });
  
  const res = await fetch(`${API_URL}/tickets?${params}`, {
    method: 'POST',
  });
  
  if (!res.ok) {
    const error = await res.json(); // Intentar capturar el error detallado de FastAPI
    throw new Error(error.detail || 'Error al crear ticket');
  }

  return res.json();
}

export async function cambiarEstadoTicket(
  id: string,
  nuevoEstado: 'abierto' | 'en_proceso' | 'cerrado'
) {
  const res = await fetch(
    `${API_URL}/tickets/${id}/estado?nuevo_estado=${nuevoEstado}`,
    { method: 'PUT' }
  );
  if (!res.ok) {
    throw new Error('Error al cambiar estado');
  }

  return res.json();
}

import { Interaccion } from '@/types/interacciones';

export async function getHistorialTicket(
  idTicket: string
): Promise<Interaccion[]> {
  const res = await fetch(
    `${API_URL}/tickets/${idTicket}/historial`,
    { cache: 'no-store' }
  );
  if (!res.ok) {
    throw new Error('Error al obtener historial');
  }

  return res.json();
}