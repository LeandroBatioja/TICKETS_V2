from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from enum import Enum

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from pydantic import BaseModel

from database import SessionLocal
from models import Usuario, Ticket, Interaccion
from redis_client import cache_usuario, enviar_tarea

app = FastAPI(title="Sistema de Tickets con Batch Worker")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las solicitudes de cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"],  # Permite todos los encabezados
)


# ======================================================
# ENUMS (coinciden EXACTAMENTE con los CHECK de Supabase)
# ======================================================

class RolUsuario(str, Enum):
    cliente = "cliente"
    operador = "operador"

class EstadoTicket(str, Enum):
    abierto = "abierto"
    en_proceso = "en_proceso"
    cerrado = "cerrado"

class PrioridadTicket(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

# ======================================================
# DEPENDENCIA DE BASE DE DATOS
# ======================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ======================================================
# CREAR USUARIO
# ======================================================

@app.post("/usuarios")
def crear_usuario(
    nombre: str,
    email: str,
    rol: RolUsuario,
    db: Session = Depends(get_db)
):
    try:
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=rol.value
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    except SQLAlchemyError as e:
        db.rollback()
        print("ERROR BD:", e)
        raise HTTPException(status_code=500, detail="Error al crear usuario")

    # Cache en Redis (no rompe si falla)
    try:
        cache_usuario(usuario.id_usuario, {
            "id_usuario": usuario.id_usuario,
            "nombre": usuario.nombre,
            "rol": usuario.rol
        })
    except Exception:
        pass

    return usuario

# ======================================================
# CREAR TICKET
# ======================================================

# -----------------------
# CREAR TICKET
# -----------------------
@app.post("/tickets")
def crear_ticket(
    id_usuario: int,  # Sigue esperando el ID por query param
    asunto: str,
    prioridad: PrioridadTicket,
    db: Session = Depends(get_db)
):
    try:
        # 1. Verificar que el usuario exista
        usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
        if not usuario:
            # Error 404 si el usuario logeado no existe (por si acaso)
            raise HTTPException(status_code=404, detail=f"Usuario con ID {id_usuario} no encontrado.")

        # 2. Crear el nuevo ticket en la BD
        nuevo_ticket = Ticket(
            id_usuario=id_usuario,
            asunto=asunto,
            estado='abierto',
            prioridad=prioridad.value
        )
        db.add(nuevo_ticket)
        db.commit()
        db.refresh(nuevo_ticket)

        # 3. Registrar interacción inicial
        interaccion = Interaccion(
            id_ticket=nuevo_ticket.id_ticket,
            autor=usuario.rol, # Usamos el rol del usuario que lo crea
            mensaje=f"Ticket creado con asunto: {asunto}"
        )
        db.add(interaccion)
        db.commit()

        # 4. Intentar cachear (manejo de errores para que no rompa la creación del ticket)
        try:
            cache_ticket(nuevo_ticket.id_ticket, {
                "asunto": nuevo_ticket.asunto,
                "estado": nuevo_ticket.estado
            })
        except Exception as e:
            print(f"Advertencia: Falló el cacheo de Redis: {e}")
            pass # No rompemos la creación del ticket por fallo de cache

        return {"mensaje": "Ticket creado exitosamente", "id_ticket": nuevo_ticket.id_ticket}

    except HTTPException as e:
        db.rollback()
        # Propaga el error 404 si el usuario no existe
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print("ERROR BD AL CREAR TICKET:", e)
        # Error 500 si hay un problema en la DB
        raise HTTPException(status_code=500, detail="Error de base de datos al crear el ticket.")
    except Exception as e:
        db.rollback()
        print("ERROR GENERAL AL CREAR TICKET:", e)
        # Error 500 para cualquier otro error imprevisto
        raise HTTPException(status_code=500, detail="Error interno del servidor al crear el ticket.")

# -----------------------
# LISTAR TODOS LOS TICKETS (OPERADOR)
# -----------------------
@app.get("/tickets")
def listar_tickets(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).order_by(Ticket.fecha_creacion.desc()).all()
    return tickets

# ======================================================
# CAMBIAR ESTADO DEL TICKET (SOLO OPERADOR)
# ======================================================

@app.put("/tickets/{id_ticket}/estado")
def cambiar_estado_ticket(
    id_ticket: int,
    nuevo_estado: EstadoTicket,
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id_ticket == id_ticket
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")

    try:
        ticket.estado = nuevo_estado.value
        db.commit()

        interaccion = Interaccion(
            id_ticket=id_ticket,
            autor="operador",
            mensaje=f"Estado actualizado a {nuevo_estado.value}"
        )
        db.add(interaccion)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        print("ERROR BD:", e)
        raise HTTPException(status_code=500, detail="Error al actualizar estado")

    try:
        enviar_tarea(id_ticket)
    except Exception:
        pass

    return {"mensaje": "Estado actualizado correctamente"}

# ======================================================
# HISTORIAL DE INTERACCIONES
# ======================================================

@app.get("/tickets/{id_ticket}/historial")
def historial_ticket(
    id_ticket: int,
    db: Session = Depends(get_db)
):
    historial = db.query(Interaccion).filter(
        Interaccion.id_ticket == id_ticket
    ).order_by(Interaccion.fecha_creacion.asc()).all()

    return historial


# -----------------------
# LISTAR TODOS LOS TICKETS
# -----------------------
@app.get("/tickets")
def listar_tickets(db: Session = Depends(get_db)):
    try:
        tickets = db.query(Ticket).all()
        return tickets
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Error al obtener tickets")

# ======================================================
# INICIO DE SESIÓN Y REGISTRO (100% CON LA BASE DE DATOS)
# ======================================================

# Esquemas de entrada para Pydantic
class UsuarioBase(BaseModel):
    nombre: str
    email: str
    rol: RolUsuario # RolUsuario ya está definido en main.py

class UsuarioCreate(UsuarioBase):
    pass 

class UsuarioLogin(BaseModel):
    email: str
    # Aquí se simula la contraseña, pero la BD solo verifica el email por simplicidad del esquema.

# -----------------------
# REGISTRO DE USUARIO (INSERT en la tabla usuarios)
# -----------------------
@app.post("/auth/register")
def register_user(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db)
):
    # 1. Verificar si el email ya existe en la BD
    existing_user = db.query(Usuario).filter(
        Usuario.email == usuario_data.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    try:
        # 2. Crear nuevo usuario en la BD
        usuario = Usuario(
            nombre=usuario_data.nombre,
            email=usuario_data.email,
            rol=usuario_data.rol.value 
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        # 3. Cache en Redis (opcional)
        try:
            cache_usuario(usuario.id_usuario, {
                "id_usuario": usuario.id_usuario,
                "nombre": usuario.nombre,
                "rol": usuario.rol
            })
        except Exception:
            pass

    except SQLAlchemyError as e:
        db.rollback()
        print("ERROR BD:", e)
        raise HTTPException(status_code=500, detail="Error al registrar usuario en la base de datos")

    return {"mensaje": "Registro exitoso", "id_usuario": usuario.id_usuario, "rol": usuario.rol}

# -----------------------
# INICIO DE SESIÓN (SELECT en la tabla usuarios)
# -----------------------
@app.post("/auth/login")
def login_user(
    usuario_login: UsuarioLogin,
    db: Session = Depends(get_db)
):
    # 1. Buscar usuario por email en la BD
    usuario = db.query(Usuario).filter(
        Usuario.email == usuario_login.email
    ).first()

    if not usuario:
        # Si el email no existe en la BD, lanza un error de credenciales
        raise HTTPException(status_code=401, detail="Credenciales inválidas (Email no encontrado)") 

    # 2. Si el usuario existe, el login es exitoso
    return {
        "mensaje": "Inicio de sesión exitoso", 
        "id": usuario.id_usuario, 
        "nombre": usuario.nombre, 
        "rol": usuario.rol
    }

# -----------------------
# OBTENER USUARIO ACTUAL (Endpoint /me - Usa la DB para obtener un usuario existente)
# -----------------------
@app.get("/me")
def get_current_user(
    db: Session = Depends(get_db)
):
    # Busca el primer usuario para simular el usuario logeado 
    usuario_simulado = db.query(Usuario).first() 

    if not usuario_simulado:
        raise HTTPException(status_code=404, detail="No hay usuarios registrados en la base de datos")

    return {
        "id": usuario_simulado.id_usuario, 
        "nombre": usuario_simulado.nombre, 
        "rol": usuario_simulado.rol
    }

