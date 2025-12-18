# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from enum import Enum as PyEnum
from datetime import datetime

# Importaciones de CORS (necesario para el frontend)
from fastapi.middleware.cors import CORSMiddleware

# ======================================================
# CONFIGURACIÓN DE FASTAPI
# ======================================================
app = FastAPI()

# Configuración de CORS

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Debe ser una lista de strings
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ======================================================
# CONFIGURACIÓN DE BASE DE DATOS (Ajusta esto a tu entorno)
# ======================================================

# Define la URL de conexión a tu base de datos PostgreSQL
# Asegúrate de que esta URL sea correcta.
DATABASE_URL = "postgresql://postgres.kcmmtuzwdfprxqqgvedk:Pucese_74086477@aws-0-us-west-2.pooler.supabase.com:6543/postgres?pgbouncer=true"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Función para obtener la sesión de la DB (Dependency)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función de cache de Redis (PLACEHOLDER: Asumimos que no falla gravemente)
def cache_usuario(id, data):
    # En un entorno real, aquí se implementaría la lógica de Redis
    print(f"DEBUG: Caché de usuario {id} actualizada.")
    pass

def cache_ticket(id, data):
    # En un entorno real, aquí se implementaría la lógica de Redis
    print(f"DEBUG: Caché de ticket {id} actualizada.")
    pass

# ======================================================
# MODELOS SQLAlchemy (Basado en tu código SQL)
# ======================================================

class RolUsuario(str, PyEnum):
    cliente = 'cliente'
    operador = 'operador'

class PrioridadTicket(str, PyEnum):
    baja = 'baja'
    media = 'media'
    alta = 'alta'

class EstadoTicket(str, PyEnum):
    abierto = 'abierto'
    en_proceso = 'en_proceso'
    cerrado = 'cerrado'


class Usuario(Base):
    __tablename__ = 'usuarios'
    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    rol = Column(Enum(RolUsuario, name='rolusuario'), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)

class Ticket(Base):
    __tablename__ = 'tickets'
    id_ticket = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey('usuarios.id_usuario'), nullable=False)
    asunto = Column(String(200), nullable=False)
    
    # 🛑 CAMBIO CLAVE: Agregar la columna 'descripcion'
    descripcion = Column(String, default="") # Usamos String sin límite de longitud
    
    estado = Column(Enum(EstadoTicket, name='estadoticket'), default='abierto')
    prioridad = Column(Enum(PrioridadTicket, name='prioridadticket'), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)
    
    estado = Column(Enum(EstadoTicket, name='estadoticket'), default='abierto')
    prioridad = Column(Enum(PrioridadTicket, name='prioridadticket'), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)
    # Relación: un ticket pertenece a un usuario
    usuario = relationship("Usuario")
    
class Interaccion(Base):
    __tablename__ = 'interacciones'
    id_interaccion = Column(Integer, primary_key=True, index=True)
    id_ticket = Column(Integer, ForeignKey('tickets.id_ticket'), nullable=False)
    autor = Column(Enum(RolUsuario, name='autorinteraccion'), nullable=False)
    mensaje = Column(String, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.now)


# Crear las tablas en la base de datos (solo la primera vez)
# Base.metadata.create_all(bind=engine)




# ======================================================
# ESQUEMAS PYDANTIC
# ======================================================

class UsuarioBase(BaseModel):
    nombre: str
    email: str
    rol: RolUsuario
    
class UsuarioCreate(UsuarioBase):
    pass 

class UsuarioLogin(BaseModel):
    email: str

class TicketCreateOperator(BaseModel):
    client_email: str
    asunto: str
    descripcion: str # 🛑 CAMBIO CLAVE: Agregado el campo descripción
    prioridad: PrioridadTicket

# ======================================================
# ENDPOINTS DE AUTENTICACIÓN
# ======================================================

@app.post("/auth/register")
def register_user(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    existing_user = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    try:
        usuario = Usuario(nombre=usuario_data.nombre, email=usuario_data.email, rol=usuario_data.rol.value)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        try:
            cache_usuario(usuario.id_usuario, {"id_usuario": usuario.id_usuario, "nombre": usuario.nombre, "rol": usuario.rol})
        except Exception: pass
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al registrar usuario en la base de datos")
    return {"mensaje": "Registro exitoso", "id_usuario": usuario.id_usuario, "rol": usuario.rol}

@app.post("/auth/login")
def login_user(usuario_login: UsuarioLogin, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == usuario_login.email).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas (Email no encontrado)") 
    return {"mensaje": "Inicio de sesión exitoso", "id": usuario.id_usuario, "nombre": usuario.nombre, "rol": usuario.rol}
    
@app.get("/me")
def get_current_user(db: Session = Depends(get_db)):
    # Busca el primer usuario para simular el usuario logeado si no hay una gestión de sesión real
    usuario_simulado = db.query(Usuario).first() 
    if not usuario_simulado:
        raise HTTPException(status_code=404, detail="No hay usuarios registrados en la base de datos")
    return {"id": usuario_simulado.id_usuario, "nombre": usuario_simulado.nombre, "rol": usuario_simulado.rol}


# ======================================================
# ENDPOINTS DE GESTIÓN DE TICKETS (ROL-BASED)
# ======================================================

# 1. LISTAR TICKETS SEGÚN ROL (GET /tickets)
@app.get("/tickets")
def listar_tickets(
    user_id: int, 
    user_role: RolUsuario,
    db: Session = Depends(get_db)
):
    """
    Lista tickets: Clientes solo ven los suyos, Operadores ven todos.
    """
    try:
        if user_role.value == 'operador':
            # El operador ve todos los tickets
            tickets = db.query(Ticket).all()
        elif user_role.value == 'cliente':
            # El cliente solo ve sus propios tickets
            tickets = db.query(Ticket).filter(Ticket.id_usuario == user_id).all()
        else:
            raise HTTPException(status_code=403, detail="Rol de usuario no válido.")
            
        return tickets
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al obtener tickets de la base de datos.")

# 2. CREAR TICKET (POST /tickets) - EXCLUSIVO PARA OPERADORES
@app.post("/tickets")
def crear_ticket(
    operator_id: int, 
    ticket_data: TicketCreateOperator,
    db: Session = Depends(get_db)
):
    """
    Crea un ticket asociándolo al cliente por su email. Solo para Operadores.
    """
    try:
        # 1. Verificar que el usuario que llama sea un operador
        operator_user = db.query(Usuario).filter(
            Usuario.id_usuario == operator_id,
            Usuario.rol == 'operador'
        ).first()
        
        if not operator_user:
            raise HTTPException(status_code=403, detail="Acceso denegado: Solo operadores pueden crear tickets.")
            
        # 2. Buscar el ID del cliente por correo
        client_user = db.query(Usuario).filter(
            Usuario.email == ticket_data.client_email,
        ).first()

        if not client_user:
            raise HTTPException(status_code=404, detail=f"Cliente con email '{ticket_data.client_email}' no encontrado.")

        # 3. Crear el nuevo ticket, asociado al ID del cliente encontrado
        nuevo_ticket = Ticket(
        id_usuario=client_user.id_usuario, 
        asunto=ticket_data.asunto,
        descripcion=ticket_data.descripcion, # 🛑 USANDO EL CAMPO DESCRIPCION
        estado='abierto',
        prioridad=ticket_data.prioridad.value
        )
        db.add(nuevo_ticket)
        db.commit()
        db.refresh(nuevo_ticket)

        # 4. Registrar interacción inicial
        interaccion = Interaccion(
            id_ticket=nuevo_ticket.id_ticket,
            autor='operador', 
            mensaje=f"Ticket creado por operador ({operator_user.nombre}) para cliente {client_user.nombre} ({client_user.email}) con asunto: {ticket_data.asunto}"
        )
        db.add(interaccion)
        db.commit()

        # 5. Cache (opcional)
        try:
            cache_ticket(nuevo_ticket.id_ticket, {"asunto": nuevo_ticket.asunto, "estado": nuevo_ticket.estado})
        except Exception:
            pass 

        return {"mensaje": "Ticket creado exitosamente por operador", "id_ticket": nuevo_ticket.id_ticket}

    except HTTPException as e:
        db.rollback()
        raise e
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error de base de datos al crear el ticket.")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error interno del servidor al crear el ticket.")


# 3. CAMBIAR ESTADO TICKET (PUT /tickets/{id}/estado)
@app.put("/tickets/{id}/estado")
def cambiar_estado_ticket(id: int, nuevo_estado: EstadoTicket, db: Session = Depends(get_db)):
    """
    Cambia el estado de un ticket y registra la interacción.
    """
    try:
        ticket = db.query(Ticket).filter(Ticket.id_ticket == id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
            
        estado_anterior = ticket.estado
        
        if estado_anterior != nuevo_estado.value:
            ticket.estado = nuevo_estado.value
            
            # Registrar interacción
            interaccion = Interaccion(
                id_ticket=id,
                autor='operador', # Asumimos que un operador realiza el cambio de estado
                mensaje=f"Estado del ticket cambiado de '{estado_anterior}' a '{nuevo_estado.value}'"
            )
            db.add(interaccion)
            db.commit()

        return {"mensaje": f"Estado del ticket {id} cambiado a {nuevo_estado.value}"}
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al cambiar el estado en la base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")


# -----------------------
# CAMBIAR PRIORIDAD TICKET (PUT /tickets/{id}/prioridad)
# -----------------------
@app.put("/tickets/{id}/prioridad")
def cambiar_prioridad_ticket(id: int, nueva_prioridad: PrioridadTicket, db: Session = Depends(get_db)):
    """
    Cambia la prioridad de un ticket y registra la interacción.
    """
    try:
        ticket = db.query(Ticket).filter(Ticket.id_ticket == id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
            
        prioridad_anterior = ticket.prioridad
        
        if prioridad_anterior != nueva_prioridad.value:
            ticket.prioridad = nueva_prioridad.value
            
            # Registrar interacción
            interaccion = Interaccion(
                id_ticket=id,
                autor='operador', # Asumimos que un operador realiza el cambio de prioridad
                mensaje=f"Prioridad del ticket cambiada de '{prioridad_anterior}' a '{nueva_prioridad.value}'"
            )
            db.add(interaccion)
            db.commit()
            db.refresh(ticket) # Recargar el ticket para tener los datos actualizados
            
            # Devolver el ticket actualizado para que el frontend lo sincronice
            return ticket
        
        return {"mensaje": "La prioridad no ha cambiado"}
        
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al cambiar la prioridad en la base de datos")
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno del servidor")



# 4. HISTORIAL TICKET (GET /tickets/{id_ticket}/historial)
@app.get("/tickets/{id_ticket}/historial")
def historial_ticket(id_ticket: int, db: Session = Depends(get_db)):
    """
    Obtiene el historial de interacciones de un ticket.
    """
    interacciones = db.query(Interaccion).filter(
        Interaccion.id_ticket == id_ticket
    ).order_by(Interaccion.fecha_creacion).all()
    
    if not interacciones:
        # Verifica si el ticket existe antes de decir que no hay historial
        ticket_exists = db.query(Ticket).filter(Ticket.id_ticket == id_ticket).first()
        if not ticket_exists:
             raise HTTPException(status_code=404, detail="Ticket no encontrado")
             
    return interacciones