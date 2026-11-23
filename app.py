"""
=====================================================================
 VetSmart - Clínica Veterinaria Inteligente (versión sin base de datos)
=====================================================================
 Todo vive en UN solo archivo. Los datos se guardan en listas y
 diccionarios de Python (en memoria) y se respaldan en un archivo
 .pkl para que no se pierdan al reiniciar.

 Para ejecutar en tu computadora:
     pip install -r requirements.txt
     streamlit run app.py

 Usuarios de prueba:
   - Administrador:   admin / admin123
   - Recepción:       recepcion / recep123
   - Veterinario:     veterinario / vet123
   - Cliente:         teléfono 6641234567 / contraseña 1234
     (o crea una cuenta nueva desde la pestaña "Soy cliente")
=====================================================================
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
from PIL import Image, ImageOps
import base64
import io
import os
import pickle
import random
import math

# ---------------------------------------------------------------------
#  CONFIGURACIÓN DE LA PÁGINA (debe ir antes que cualquier otra cosa)
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="VetSmart",
    layout="wide",
    initial_sidebar_state="auto",
)

ARCHIVO_RESPALDO = "vetsmart_respaldo.pkl"
ZONA_HORARIA = ZoneInfo("America/Tijuana")

# Catálogos fijos
ESPECIES = ["Perro", "Gato", "Conejo", "Ave", "Hámster", "Tortuga", "Iguana", "Hurón", "Otro"]
TAMANOS = ["Chico", "Mediano", "Grande"]
SERVICIOS = ["Consulta general", "Vacunación", "Desparasitación", "Baño y estética",
             "Revisión de seguimiento", "Valoración para cirugía"]
ESTADOS_CITA = ["Pendiente", "Confirmada", "Completada", "Cancelada", "No asistió"]
ESTADOS_MASCOTA = ["Activo", "Inactivo", "Fallecido"]

# Vacunas: cada cuántos días se repite y qué producto del inventario descuenta
VACUNAS = {
    "Rabia": {"dias": 365, "producto": "Vacuna antirrábica"},
    "Múltiple canina (DHPP)": {"dias": 365, "producto": "Vacuna múltiple canina"},
    "Triple felina": {"dias": 365, "producto": "Vacuna triple felina"},
    "Bordetella (tos de las perreras)": {"dias": 180, "producto": "Vacuna Bordetella"},
    "Leptospirosis": {"dias": 365, "producto": "Vacuna Leptospirosis"},
}

# Colores para cada estado de cita
COLOR_ESTADO = {
    "Pendiente": "#8A9BB0",
    "Confirmada": "#2F8CEB",
    "Completada": "#25A36F",
    "Cancelada": "#E05A5A",
    "No asistió": "#E8A33D",
}
COLOR_MASCOTA = {"Activo": "#25A36F", "Inactivo": "#8A9BB0", "Fallecido": "#12304D"}
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


# =====================================================================
#  ESTILOS (azul claro y blanco)
# =====================================================================
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
:root {
    --azul: #2F8CEB; --azul-oscuro: #1663B8; --azul-claro: #EAF4FF;
    --fondo: #F6FAFF; --texto: #12304D; --suave: #5B7897; --borde: #DCEAF8;
}
html, body, .stApp, button, input, textarea { font-family: 'Plus Jakarta Sans', sans-serif; }
.stApp { background-color: var(--fondo); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1300px; }
h1, h2, h3 { color: var(--texto); letter-spacing: -0.02em; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #EEF6FF 100%);
    border-right: 1px solid var(--borde);
}
section[data-testid="stSidebar"] [role="radiogroup"] label {
    width: 100%; padding: 0.4rem 0.7rem; border-radius: 10px;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--azul-claro); }
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: var(--azul); }
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color: #FFFFFF !important; font-weight: 600; }

[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid var(--borde); border-radius: 14px; padding: 0.8rem 1rem;
}
[data-testid="stMetricLabel"] p { color: var(--suave); font-weight: 600; }
[data-testid="stMetricValue"] { color: var(--texto); font-weight: 800; }

.titulo { font-size: 1.8rem; font-weight: 800; color: var(--texto); margin: 0; letter-spacing: -0.03em; }
.subtitulo { color: var(--suave); margin: 0 0 1.2rem 0; }
.tarjeta {
    background: #FFFFFF; border: 1px solid var(--borde); border-radius: 16px;
    padding: 0.9rem 1.1rem; margin-bottom: 0.6rem;
}
.tarjeta-azul {
    background: linear-gradient(135deg, #2F8CEB 0%, #5AAAF8 100%);
    border-radius: 18px; padding: 1.2rem 1.3rem; margin-bottom: 0.8rem; color: #FFFFFF;
}
.tarjeta-azul * { color: #FFFFFF !important; }
.insignia {
    display: inline-block; padding: 0.1rem 0.6rem; border-radius: 999px;
    font-size: 0.75rem; font-weight: 700; color: #FFFFFF; white-space: nowrap;
}
.dato { color: var(--suave); font-size: 0.85rem; margin: 0; }
.alerta-roja {
    background: #FDECEC; border-left: 4px solid #E05A5A; padding: 0.5rem 0.8rem;
    border-radius: 8px; color: #8A2A2A; font-size: 0.9rem; margin: 0.3rem 0 0.6rem 0;
}
.foto-mascota { width: 100%; max-width: 260px; aspect-ratio: 1 / 1; object-fit: cover; border-radius: 14px; display: block; }
.foto-vacia {
    width: 100%; max-width: 260px; aspect-ratio: 1 / 1; border-radius: 14px; background: var(--azul-claro);
    display: flex; align-items: center; justify-content: center; font-size: 3rem; flex-shrink: 0;
    font-weight: 800; color: var(--azul-oscuro);
}
.fila-mascota { display: flex; gap: 14px; align-items: center; }
.fila-mascota p { margin: 0.1rem 0; }
.tira-fotos { display: flex; gap: 10px; overflow-x: auto; padding: 4px 4px 6px 4px; }
.tira-fotos .opcion { text-align: center; font-weight: 700; font-size: 0.85rem; color: var(--texto); }
.tira-fotos .elegida .foto-mascota, .tira-fotos .elegida .foto-vacia { outline: 3px solid var(--azul); }
.hero {
    background: linear-gradient(145deg, #2F8CEB 0%, #6DB5FF 100%);
    border-radius: 26px; padding: 2.3rem 2rem; color: #FFFFFF; min-height: 440px;
}
.hero h1 { color: #FFFFFF; font-size: 2.5rem; font-weight: 800; margin: 0.5rem 0; }
.hero p { color: #EAF4FF; font-size: 1rem; line-height: 1.5; }
.hero .item { background: rgba(255,255,255,0.16); border-radius: 14px; padding: 0.65rem 0.9rem; margin-top: 0.55rem; font-weight: 600; }
.pie { text-align: center; color: #93A9BF; font-size: 0.78rem; margin-top: 2rem; }
[data-testid="InputInstructions"] { display: none !important; }
/* En celular ocultamos la imagen grande del acceso */
@media (max-width: 640px) { .hero { display: none; } }
</style>
"""

CSS_MOVIL = """
<style>
.block-container { max-width: 560px !important; padding: 1rem 1rem 3rem 1rem !important; }
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
.stButton button, .stLinkButton a, .stFormSubmitButton button { min-height: 2.8rem; border-radius: 12px; }
</style>
"""

CSS_SIN_MENU = """
<style>
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# =====================================================================
#  FECHAS Y HORAS (siempre con la hora de Tijuana)
# =====================================================================
def ahora():
    """Fecha y hora actual de Tijuana (el servidor en la nube usa otra zona)."""
    return datetime.now(ZONA_HORARIA).replace(tzinfo=None)


def hoy():
    return ahora().date()


def fecha_bonita(fecha):
    """Convierte una fecha a texto: 'Lunes 9 nov 2026'."""
    return f"{DIAS_SEMANA[fecha.weekday()]} {fecha.day} {MESES[fecha.month - 1]} {fecha.year}"


def fecha_corta(fecha):
    return f"{fecha.day} {MESES[fecha.month - 1]} {fecha.year}"


# =====================================================================
#  DATOS DE EJEMPLO
#  Se generan con fechas relativas a hoy para que siempre se vean
#  citas pasadas (para el tablero) y citas próximas (para la agenda).
# =====================================================================
def crear_datos_ejemplo():
    rng = random.Random(7)  # semilla fija: siempre salen los mismos datos
    dia_hoy = hoy()

    usuarios = [
        {"Usuario": "admin", "Contrasena": "admin123", "Nombre": "Gerente VetSmart",
         "Rol": "Administrador", "Activo": True},
        {"Usuario": "recepcion", "Contrasena": "recep123", "Nombre": "Laura Méndez",
         "Rol": "Recepción", "Activo": True},
        {"Usuario": "veterinario", "Contrasena": "vet123", "Nombre": "Dra. Paola Ruiz",
         "Rol": "Veterinario", "Activo": True},
    ]

    nombres_clientes = [
        ("Misael Félix", "6641234567"), ("Ana López", "6642345678"), ("Carlos Pérez", "6643456789"),
        ("María García", "6644567890"), ("Luis Hernández", "6645678901"), ("Sofía Martínez", "6646789012"),
        ("Roberto Díaz", "6647890123"), ("Fernanda Torres", "6648901234"), ("Jorge Ramírez", "6649012345"),
        ("Valeria Castro", "6640123456"), ("Diego Morales", "6641122334"), ("Paulina Reyes", "6642233445"),
    ]
    clientes = []
    for i, (nombre, telefono) in enumerate(nombres_clientes, start=1):
        clientes.append({
            "ID": f"C{i:03d}", "Nombre": nombre, "Telefono": telefono,
            "Correo": nombre.split()[0].lower() + "@correo.com",
            "Contrasena": "1234",
            "Alta": dia_hoy - timedelta(days=rng.randint(60, 400)),
        })

    lista_mascotas = [
        ("Firulais", "Perro", "Mestizo", "Macho", 5, 18.5, "Mediano"),
        ("Luna", "Gato", "Siamés", "Hembra", 3, 4.2, "Chico"),
        ("Rocky", "Perro", "Pastor alemán", "Macho", 7, 34.0, "Grande"),
        ("Michi", "Gato", "Doméstico", "Hembra", 2, 3.8, "Chico"),
        ("Coco", "Perro", "Chihuahua", "Macho", 9, 2.9, "Chico"),
        ("Canela", "Perro", "Labrador", "Hembra", 4, 29.0, "Grande"),
        ("Copito", "Conejo", "Cabeza de león", "Macho", 2, 1.6, "Chico"),
        ("Simba", "Gato", "Persa", "Macho", 6, 5.1, "Chico"),
        ("Max", "Perro", "Schnauzer", "Macho", 5, 8.7, "Chico"),
        ("Kiwi", "Ave", "Perico australiano", "Hembra", 1, 0.04, "Chico"),
        ("Bruno", "Perro", "Bulldog francés", "Macho", 3, 12.3, "Mediano"),
        ("Nala", "Gato", "Bengalí", "Hembra", 4, 4.6, "Chico"),
        ("Toby", "Perro", "Beagle", "Macho", 8, 14.1, "Mediano"),
        ("Hammy", "Hámster", "Sirio", "Macho", 1, 0.12, "Chico"),
        ("Daisy", "Perro", "Golden retriever", "Hembra", 6, 31.2, "Grande"),
        ("Tortu", "Tortuga", "Orejas rojas", "Hembra", 10, 0.8, "Chico"),
        ("Salem", "Gato", "Doméstico negro", "Macho", 7, 5.4, "Chico"),
        ("Lola", "Perro", "Poodle", "Hembra", 4, 6.2, "Chico"),
        ("Duke", "Perro", "Husky siberiano", "Macho", 5, 25.6, "Grande"),
        ("Pelusa", "Gato", "Angora", "Hembra", 11, 4.0, "Chico"),
    ]
    alergias = ["", "", "", "", "Penicilina", "Pollo", "", "Picadura de pulga", "", ""]
    mascotas = []
    for i, (nombre, especie, raza, sexo, edad, peso, tamano) in enumerate(lista_mascotas, start=1):
        # Las 2 primeras son del cliente de prueba (Misael), las demás se reparten
        if i <= 2:
            dueno = "C001"
        else:
            dueno = clientes[(i % (len(clientes) - 1)) + 1]["ID"]
        mascotas.append({
            "ID": f"M{i:03d}", "Nombre": nombre, "Especie": especie, "Raza": raza,
            "Sexo": sexo, "Edad": edad, "Peso": peso, "Tamano": tamano,
            "Cliente": dueno, "Estado": "Activo", "Alergias": rng.choice(alergias),
            "Foto": None, "Alta": dia_hoy - timedelta(days=rng.randint(30, 380)),
        })
    mascotas[15]["Estado"] = "Inactivo"
    mascotas[19]["Estado"] = "Fallecido"

    productos = [
        # Nombre, categoría, unidad, existencia, mínimo, días para caducar
        ("Vacuna antirrábica", "Vacuna", "dosis", 24, 10, 210),
        ("Vacuna múltiple canina", "Vacuna", "dosis", 8, 10, 150),
        ("Vacuna triple felina", "Vacuna", "dosis", 12, 6, 25),
        ("Vacuna Bordetella", "Vacuna", "dosis", 5, 4, 300),
        ("Vacuna Leptospirosis", "Vacuna", "dosis", 0, 4, 120),
        ("Desparasitante oral (tableta)", "Desparasitante", "tableta", 60, 20, 400),
        ("Pipeta antipulgas", "Desparasitante", "pieza", 18, 10, 500),
        ("Amoxicilina 250 mg", "Antibiótico", "tableta", 90, 30, 18),
        ("Meloxicam 1.5 mg/ml", "Antiinflamatorio", "frasco", 6, 3, 260),
        ("Suero fisiológico 500 ml", "Material", "frasco", 14, 8, 700),
        ("Shampoo medicado", "Estética", "frasco", 4, 5, 365),
        ("Gasas estériles", "Material", "paquete", 40, 15, 900),
    ]
    lista_productos = []
    for i, (nombre, categoria, unidad, existencia, minimo, dias) in enumerate(productos, start=1):
        lista_productos.append({
            "ID": f"P{i:03d}", "Nombre": nombre, "Categoria": categoria, "Unidad": unidad,
            "Existencia": existencia, "Minimo": minimo, "Caducidad": dia_hoy + timedelta(days=dias),
        })

    # ---- Citas pasadas (para el tablero BI) ----
    citas = []
    consultas = []
    vacunas_aplicadas = []
    movimientos = []
    horas = horas_del_dia()
    contador = 1
    for dias_atras in range(180, 0, -1):
        dia = dia_hoy - timedelta(days=dias_atras)
        if dia.weekday() == 6:
            continue  # domingo cerrado
        # Sábados y lunes hay más movimiento
        cantidad = rng.randint(1, 4) + (1 if dia.weekday() in (0, 5) else 0)
        horas_dia = rng.sample(horas, cantidad)
        for hora in sorted(horas_dia):
            mascota = rng.choice(mascotas[:19])
            servicio = rng.choices(SERVICIOS, weights=[30, 22, 14, 18, 10, 6])[0]
            estado = rng.choices(["Completada", "No asistió", "Cancelada"], weights=[78, 10, 12])[0]
            citas.append({
                "ID": f"CT{contador:04d}", "Mascota": mascota["ID"], "Cliente": mascota["Cliente"],
                "Servicio": servicio, "Fecha": dia, "Hora": hora, "Estado": estado,
                "Notas": "", "Creada": datetime.combine(dia - timedelta(days=rng.randint(1, 10)), time(10, 0)),
                "Confirmada_en": None,
            })
            if estado == "Completada":
                consultas.append({
                    "ID": f"CO{len(consultas) + 1:04d}", "Cita": f"CT{contador:04d}",
                    "Mascota": mascota["ID"], "Fecha": dia, "Veterinario": "Dra. Paola Ruiz",
                    "Motivo": servicio, "Peso": mascota["Peso"], "Temperatura": round(rng.uniform(37.8, 39.2), 1),
                    "Diagnostico": rng.choice(["Sano", "Otitis leve", "Dermatitis", "Control de peso",
                                               "Gastroenteritis leve", "Revisión dental"]),
                    "Tratamiento": rng.choice(["Ninguno", "Limpieza de oídos", "Dieta blanda 3 días",
                                               "Baño medicado semanal", "Antibiótico 7 días"]),
                    "Medicamento": "", "Cantidad": 0,
                })
                if servicio == "Vacunación":
                    if mascota["Especie"] == "Gato":
                        vacuna = "Triple felina"
                    else:
                        vacuna = rng.choice(["Rabia", "Múltiple canina (DHPP)", "Bordetella (tos de las perreras)"])
                    vacunas_aplicadas.append({
                        "Mascota": mascota["ID"], "Vacuna": vacuna, "Fecha": dia,
                        "Proxima": dia + timedelta(days=VACUNAS[vacuna]["dias"]),
                    })
                    movimientos.append({"Fecha": dia, "Producto": VACUNAS[vacuna]["producto"],
                                        "Tipo": "Salida", "Cantidad": 1, "Motivo": f"Vacuna a {mascota['Nombre']}"})
                if servicio == "Desparasitación":
                    movimientos.append({"Fecha": dia, "Producto": "Desparasitante oral (tableta)",
                                        "Tipo": "Salida", "Cantidad": 1, "Motivo": f"Desparasitación de {mascota['Nombre']}"})
            contador += 1

    # ---- Citas próximas (para la agenda y confirmaciones) ----
    for dias_adelante in range(0, 15):
        dia = dia_hoy + timedelta(days=dias_adelante)
        if dia.weekday() == 6:
            continue
        cantidad = rng.randint(2, 4)
        horas_dia = rng.sample(horas, cantidad)
        for hora in sorted(horas_dia):
            if dia == dia_hoy and hora < "12:00":
                continue  # que la agenda de hoy tenga citas por atender
            mascota = rng.choice(mascotas[:19])
            if mascota["Estado"] != "Activo":
                continue
            estado = rng.choice(["Pendiente", "Pendiente", "Confirmada"])
            citas.append({
                "ID": f"CT{contador:04d}", "Mascota": mascota["ID"], "Cliente": mascota["Cliente"],
                "Servicio": rng.choice(SERVICIOS), "Fecha": dia, "Hora": hora, "Estado": estado,
                "Notas": "", "Creada": ahora() - timedelta(days=2), "Confirmada_en": None,
            })
            contador += 1

    # Pocas entradas de inventario para que se vea el historial
    for p in lista_productos[:6]:
        movimientos.append({"Fecha": dia_hoy - timedelta(days=rng.randint(20, 90)), "Producto": p["Nombre"],
                            "Tipo": "Entrada", "Cantidad": 20, "Motivo": "Compra a proveedor"})

    return {
        "usuarios": usuarios,
        "clientes": clientes,
        "mascotas": mascotas,
        "citas": citas,
        "consultas": consultas,
        "vacunas_aplicadas": vacunas_aplicadas,
        "productos": lista_productos,
        "movimientos": movimientos,
        "confirmaciones": [],
        "auditoria": [{"Fecha": ahora().strftime("%Y-%m-%d %H:%M:%S"), "Usuario": "Sistema",
                       "Acción": "Sistema iniciado con datos de ejemplo"}],
        "config": {"clinica": "VetSmart Otay", "whatsapp": "6641234567", "url_publica": ""},
    }


# =====================================================================
#  ALMACÉN COMPARTIDO
#  st.cache_resource hace que TODOS los usuarios (computadora de la
#  clínica, del veterinario y celulares) vean los mismos datos.
#  Si usáramos st.session_state, cada quien tendría su propia copia.
# =====================================================================
@st.cache_resource
def obtener_datos():
    if os.path.exists(ARCHIVO_RESPALDO):
        try:
            with open(ARCHIVO_RESPALDO, "rb") as archivo:
                datos = pickle.load(archivo)
            actualizar_roles(datos)
            return datos
        except Exception:
            pass  # si el respaldo está dañado, empezamos de nuevo
    return crear_datos_ejemplo()


def actualizar_roles(datos):
    """Si el respaldo viene de la versión anterior (rol 'Administración'),
    lo cambiamos a 'Administrador' y agregamos el usuario de recepción."""
    for u in datos["usuarios"]:
        if u["Rol"] == "Administración":
            u["Rol"] = "Administrador"
    if not any(u["Rol"] == "Recepción" for u in datos["usuarios"]):
        datos["usuarios"].append({"Usuario": "recepcion", "Contrasena": "recep123", "Nombre": "Laura Méndez",
                                  "Rol": "Recepción", "Activo": True})


def guardar():
    """Guarda una copia de todos los datos en el archivo .pkl."""
    try:
        with open(ARCHIVO_RESPALDO, "wb") as archivo:
            pickle.dump(DATOS, archivo)
    except Exception as error:
        print("No se pudo guardar el respaldo:", error)


def bitacora(accion):
    """Registra una acción en la bitácora con fecha, hora y usuario."""
    usuario = st.session_state.get("usuario")
    nombre = usuario["Nombre"] if usuario else "Público"
    DATOS["auditoria"].append({"Fecha": ahora().strftime("%Y-%m-%d %H:%M:%S"),
                               "Usuario": nombre, "Acción": accion})
    guardar()


def nuevo_id(lista, prefijo, digitos=3):
    """Genera el siguiente ID: M001, M002... sin repetir."""
    numero = len(lista) + 1
    ids = [elemento["ID"] for elemento in lista]
    while f"{prefijo}{numero:0{digitos}d}" in ids:
        numero += 1
    return f"{prefijo}{numero:0{digitos}d}"


# =====================================================================
#  BÚSQUEDAS
# =====================================================================
def buscar(lista, id_buscado):
    for elemento in lista:
        if elemento["ID"] == id_buscado:
            return elemento
    return None


def mascota(id_mascota):
    return buscar(DATOS["mascotas"], id_mascota)


def cliente(id_cliente):
    return buscar(DATOS["clientes"], id_cliente)


def producto_por_nombre(nombre):
    for p in DATOS["productos"]:
        if p["Nombre"] == nombre:
            return p
    return None


def mascotas_de(id_cliente):
    return [m for m in DATOS["mascotas"] if m["Cliente"] == id_cliente]


def nombre_mascota(id_mascota):
    m = mascota(id_mascota)
    return m["Nombre"] if m else "?"


def nombre_cliente(id_cliente):
    c = cliente(id_cliente)
    return c["Nombre"] if c else "?"


# =====================================================================
#  REGLAS DE LA AGENDA
# =====================================================================
def horas_del_dia():
    """Horario de lunes a sábado de 9:00 a 18:00, citas cada 30 minutos."""
    horas = []
    actual = datetime.combine(date.today(), time(9, 0))
    fin = datetime.combine(date.today(), time(18, 0))
    while actual < fin:
        horas.append(actual.strftime("%H:%M"))
        actual += timedelta(minutes=30)
    return horas


def horas_libres(fecha):
    """Horas disponibles de un día: sin domingos, sin horas ocupadas ni pasadas."""
    if fecha.weekday() == 6 or fecha < hoy():
        return []
    ocupadas = [c["Hora"] for c in DATOS["citas"]
                if c["Fecha"] == fecha and c["Estado"] not in ("Cancelada",)]
    libres = [h for h in horas_del_dia() if h not in ocupadas]
    if fecha == hoy():
        hora_actual = ahora().strftime("%H:%M")
        libres = [h for h in libres if h > hora_actual]
    return libres


def crear_cita(id_mascota, servicio, fecha, hora, notas=""):
    m = mascota(id_mascota)
    cita = {
        "ID": nuevo_id(DATOS["citas"], "CT", 4), "Mascota": id_mascota, "Cliente": m["Cliente"],
        "Servicio": servicio, "Fecha": fecha, "Hora": hora, "Estado": "Pendiente",
        "Notas": notas, "Creada": ahora(), "Confirmada_en": None,
    }
    DATOS["citas"].append(cita)
    bitacora(f"Cita {cita['ID']} creada para {m['Nombre']} el {fecha_corta(fecha)} a las {hora}")
    return cita


def horas_para_cita(cita):
    """Cuántas horas faltan para la cita."""
    momento = datetime.combine(cita["Fecha"], datetime.strptime(cita["Hora"], "%H:%M").time())
    return (momento - ahora()).total_seconds() / 3600


def puede_cancelar(cita):
    """El cliente solo puede cancelar en línea con 48 horas o más de anticipación."""
    return cita["Estado"] in ("Pendiente", "Confirmada") and horas_para_cita(cita) >= 48


def url_de_la_app():
    """Dirección pública de la app (se detecta sola en Streamlit Cloud)."""
    url = DATOS["config"].get("url_publica", "").strip()
    if not url:
        try:
            url = st.context.url or ""
        except Exception:
            url = ""
    return url.split("?")[0].rstrip("/")


def enlace_whatsapp(telefono, mensaje):
    """Arma el enlace de WhatsApp con el mensaje ya escrito (México = 52)."""
    numero = "".join(ch for ch in str(telefono) if ch.isdigit())
    if len(numero) == 10:
        numero = "52" + numero
    return f"https://wa.me/{numero}?text={quote(mensaje)}"


def mensaje_recordatorio(cita):
    m = mascota(cita["Mascota"])
    c = cliente(cita["Cliente"])
    enlace = f"{url_de_la_app()}/?cita={cita['ID']}"
    return (f"Hola {c['Nombre'].split()[0]}, te saludamos de {DATOS['config']['clinica']}.\n"
            f"Te recordamos la cita de {m['Nombre']} ({cita['Servicio']}) el "
            f"{fecha_bonita(cita['Fecha'])} a las {cita['Hora']}.\n\n"
            f"Confirma o cancela aquí: {enlace}")


# =====================================================================
#  INVENTARIO
# =====================================================================
def descontar_producto(nombre, cantidad, motivo):
    """Resta existencia y registra el movimiento. Devuelve True si alcanzó."""
    p = producto_por_nombre(nombre)
    if p is None or p["Existencia"] < cantidad:
        return False
    p["Existencia"] -= cantidad
    DATOS["movimientos"].append({"Fecha": hoy(), "Producto": nombre, "Tipo": "Salida",
                                 "Cantidad": cantidad, "Motivo": motivo})
    return True


def estado_producto(p):
    dias = (p["Caducidad"] - hoy()).days
    if dias < 0:
        return "Caducado"
    if p["Existencia"] == 0:
        return "Agotado"
    if dias <= 30:
        return "Por caducar"
    if p["Existencia"] <= p["Minimo"]:
        return "Stock bajo"
    return "OK"


def consumo_mensual(nombre):
    """Promedio de salidas por mes en los últimos 90 días."""
    limite = hoy() - timedelta(days=90)
    total = sum(mv["Cantidad"] for mv in DATOS["movimientos"]
                if mv["Producto"] == nombre and mv["Tipo"] == "Salida" and mv["Fecha"] >= limite)
    return total / 3


# =====================================================================
#  FOTOS
# =====================================================================
def preparar_foto(archivo):
    """Reduce la foto a 600 px para que no ocupe mucha memoria."""
    imagen = Image.open(archivo)
    imagen = ImageOps.exif_transpose(imagen)  # corrige fotos giradas del celular
    imagen = imagen.convert("RGB")
    imagen.thumbnail((600, 600))
    salida = io.BytesIO()
    imagen.save(salida, format="JPEG", quality=82)
    return salida.getvalue()


def foto_html(m, alto=None):
    """Devuelve la foto de la mascota como HTML (o un emoji si no tiene)."""
    estilo = f"style='height:{alto}px;width:{alto}px;font-size:{alto // 2}px;'" if alto else ""
    if m.get("Foto"):
        codigo = base64.b64encode(m["Foto"]).decode()
        return f"<img class='foto-mascota' {estilo} src='data:image/jpeg;base64,{codigo}'>"
    inicial = m["Nombre"][0].upper()  # sin foto: mostramos la inicial del nombre
    return f"<div class='foto-vacia' {estilo}>{inicial}</div>"


# =====================================================================
#  PIEZAS VISUALES
# =====================================================================
def encabezado(titulo, descripcion=""):
    st.markdown(f"<div class='titulo'>{titulo}</div><div class='subtitulo'>{descripcion}</div>",
                unsafe_allow_html=True)


def insignia(texto, color):
    return f"<span class='insignia' style='background:{color};'>{texto}</span>"


def tarjeta_cita(cita, mostrar_dueno=True):
    m = mascota(cita["Mascota"])
    dueno = f" · {nombre_cliente(cita['Cliente'])}" if mostrar_dueno else ""
    st.markdown(
        f"<div class='tarjeta'><b>{cita['Hora']}</b> · "
        f"<b>{m['Nombre']}</b>{dueno}<br>"
        f"<span class='dato'>{cita['Servicio']} · {fecha_bonita(cita['Fecha'])}</span> "
        f"{insignia(cita['Estado'], COLOR_ESTADO[cita['Estado']])}</div>",
        unsafe_allow_html=True,
    )


def tabla_citas(citas):
    """Convierte una lista de citas a una tabla bonita."""
    filas = []
    for c in citas:
        filas.append({"ID": c["ID"], "Fecha": c["Fecha"], "Hora": c["Hora"],
                      "Mascota": nombre_mascota(c["Mascota"]), "Dueño": nombre_cliente(c["Cliente"]),
                      "Servicio": c["Servicio"], "Estado": c["Estado"]})
    return pd.DataFrame(filas)


def estilo_grafica(figura, alto=320):
    figura.update_layout(
        height=alto, margin=dict(l=10, r=10, t=50, b=10),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#12304D"),
        title_font=dict(size=15), showlegend=False,
    )
    figura.update_xaxes(showgrid=False, title=None)
    figura.update_yaxes(gridcolor="#EEF3F9", title=None)
    return figura


def selector_mascota(lista, clave):
    """Muestra las fotos de las mascotas y botones con su nombre para elegir una.
    Devuelve el ID de la mascota elegida."""
    if len(lista) == 1:
        return lista[0]["ID"]
    nombres = {f"{m['Nombre']} ({m['ID']})": m["ID"] for m in lista}
    elegida = st.session_state.get(clave + "_id", lista[0]["ID"])
    # Tira de fotos: la mascota elegida lleva borde azul
    html = "<div class='tira-fotos'>"
    for m in lista:
        clase = "opcion elegida" if m["ID"] == elegida else "opcion"
        html += f"<div class='{clase}'>{foto_html(m, 84)}<div>{m['Nombre']}</div></div>"
    st.markdown(html + "</div>", unsafe_allow_html=True)
    actual = [texto for texto, id_m in nombres.items() if id_m == elegida][0]
    texto = st.pills("Elige", list(nombres.keys()), default=actual, key=clave, label_visibility="collapsed")
    if texto and nombres[texto] != elegida:
        st.session_state[clave + "_id"] = nombres[texto]
        st.rerun()
    return elegida


def carnet_mascota(m):
    """Carnet digital: foto, datos y vacunas con su próxima dosis."""
    c = cliente(m["Cliente"])
    col_foto, col_datos = st.columns([1, 2])
    with col_foto:
        st.markdown(foto_html(m), unsafe_allow_html=True)
    with col_datos:
        st.markdown(
            f"<div class='tarjeta-azul'><p style='margin:0;font-size:0.8rem;letter-spacing:0.1em;'>"
            f"CARNET DIGITAL · {DATOS['config']['clinica'].upper()}</p>"
            f"<h2 style='margin:0.2rem 0;'>{m['Nombre']}</h2>"
            f"<p style='margin:0;'>{m['Especie']} · {m['Raza']} · {m['Sexo']} · {m['Edad']} años · "
            f"{m['Peso']} kg</p><p style='margin:0.3rem 0 0 0;'>Dueño: {c['Nombre'] if c else '?'} · "
            f"ID {m['ID']}</p></div>",
            unsafe_allow_html=True,
        )
        st.markdown(insignia(m["Estado"], COLOR_MASCOTA[m["Estado"]]), unsafe_allow_html=True)
        if m["Alergias"]:
            st.markdown(f"<div class='alerta-roja'>Alergia: <b>{m['Alergias']}</b></div>",
                        unsafe_allow_html=True)

    st.markdown("##### Vacunas")
    vacunas = [v for v in DATOS["vacunas_aplicadas"] if v["Mascota"] == m["ID"]]
    if vacunas:
        filas = []
        for v in sorted(vacunas, key=lambda x: x["Fecha"], reverse=True):
            dias = (v["Proxima"] - hoy()).days
            if dias < 0:
                situacion = "Vencida"
            elif dias <= 30:
                situacion = "Próxima"
            else:
                situacion = "Al día"
            filas.append({"Vacuna": v["Vacuna"], "Aplicada": v["Fecha"],
                          "Próxima dosis": v["Proxima"], "Situación": situacion})
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    else:
        st.info("Aún no tiene vacunas registradas.")


# =====================================================================
#  PANTALLA DE ACCESO
# =====================================================================
def pantalla_acceso():
    st.markdown(CSS_SIN_MENU, unsafe_allow_html=True)
    col_hero, col_form = st.columns([1.2, 1], gap="large")

    with col_hero:
        st.markdown(
            """
            <div class='hero'>
                <p style='font-weight:800;letter-spacing:0.12em;font-size:0.8rem;margin:0;'>VETSMART</p>
                <h1>Clínica Veterinaria Inteligente</h1>
                <p>Salud al día para tu mascota, tranquilidad total para ti.</p>
                <div class='item'>Agenda inteligente sin dobles citas</div>
                <div class='item'>Confirmación de citas por WhatsApp</div>
                <div class='item'>Expediente y carnet de vacunas digital</div>
                <div class='item'>Inventario con alertas de caducidad</div>
                <div class='item'>Tablero de indicadores para decidir mejor</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_form:
        st.markdown("<div class='titulo'>¡Bienvenido!</div><div class='subtitulo'>Elige cómo quieres entrar.</div>",
                    unsafe_allow_html=True)
        tab_personal, tab_cliente, tab_registro = st.tabs(["Personal", "Soy cliente", "Crear cuenta"])

        with tab_personal:
            with st.form("form_personal"):
                usuario = st.text_input("Usuario", placeholder="admin, recepcion o veterinario")
                contrasena = st.text_input("Contraseña", type="password")
                entrar = st.form_submit_button("Iniciar sesión", type="primary", width="stretch")
            if entrar:
                encontrado = None
                for u in DATOS["usuarios"]:
                    if u["Usuario"] == usuario.strip().lower() and u["Contrasena"] == contrasena and u["Activo"]:
                        encontrado = u
                if encontrado:
                    st.session_state.usuario = {"Tipo": encontrado["Rol"], "Nombre": encontrado["Nombre"],
                                                "Usuario": encontrado["Usuario"]}
                    bitacora(f"{encontrado['Nombre']} inició sesión")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
            st.caption("Prueba: **admin / admin123** · **recepcion / recep123** · **veterinario / vet123**")

        with tab_cliente:
            with st.form("form_cliente"):
                telefono = st.text_input("Teléfono (10 dígitos)", max_chars=10)
                contrasena = st.text_input("Contraseña", type="password", key="pwd_cliente")
                entrar = st.form_submit_button("Entrar", type="primary", width="stretch")
            if entrar:
                encontrado = None
                for c in DATOS["clientes"]:
                    if c["Telefono"] == telefono.strip() and c["Contrasena"] == contrasena:
                        encontrado = c
                if encontrado:
                    st.session_state.usuario = {"Tipo": "Cliente", "Nombre": encontrado["Nombre"],
                                                "ID": encontrado["ID"]}
                    bitacora(f"Cliente {encontrado['Nombre']} entró desde la app")
                    st.rerun()
                else:
                    st.error("Teléfono o contraseña incorrectos.")
            st.caption("Prueba: **6641234567 / 1234**")

        with tab_registro:
            with st.form("form_registro"):
                nombre = st.text_input("Nombre completo")
                telefono = st.text_input("Teléfono (10 dígitos)", max_chars=10, key="tel_registro")
                correo = st.text_input("Correo (opcional)")
                contrasena = st.text_input("Crea una contraseña", type="password", key="pwd_registro")
                crear = st.form_submit_button("Crear mi cuenta", type="primary", width="stretch")
            if crear:
                telefono = telefono.strip()
                if not nombre.strip() or len(contrasena) < 4:
                    st.error("Escribe tu nombre y una contraseña de al menos 4 caracteres.")
                elif not (telefono.isdigit() and len(telefono) == 10):
                    st.error("El teléfono debe tener 10 dígitos.")
                elif any(c["Telefono"] == telefono for c in DATOS["clientes"]):
                    st.error("Ese teléfono ya tiene cuenta. Entra en la pestaña 'Soy cliente'.")
                else:
                    nuevo = {"ID": nuevo_id(DATOS["clientes"], "C"), "Nombre": nombre.strip(),
                             "Telefono": telefono, "Correo": correo.strip(), "Contrasena": contrasena,
                             "Alta": hoy()}
                    DATOS["clientes"].append(nuevo)
                    st.session_state.usuario = {"Tipo": "Cliente", "Nombre": nuevo["Nombre"], "ID": nuevo["ID"]}
                    bitacora(f"Nuevo cliente registrado desde la app: {nuevo['Nombre']}")
                    st.rerun()

    st.markdown("<p class='pie'>Modelo de Negocio e Innovación · UABC · FCA</p>", unsafe_allow_html=True)


# =====================================================================
#  PÁGINA PÚBLICA: CONFIRMAR CITA DESDE WHATSAPP (?cita=CT0001)
# =====================================================================
def pagina_confirmar_cita(id_cita):
    st.markdown(CSS_MOVIL, unsafe_allow_html=True)
    cita = buscar(DATOS["citas"], id_cita)
    st.markdown(f"<div class='titulo'>{DATOS['config']['clinica']}</div>", unsafe_allow_html=True)
    if cita is None:
        st.error("No encontramos esa cita. Revisa el enlace o comunícate con la clínica.")
        return

    m = mascota(cita["Mascota"])
    st.markdown(
        f"<div class='tarjeta fila-mascota'>{foto_html(m, 110)}<div><b style='font-size:1.3rem;'>{m['Nombre']}</b>"
        f"<p><b>{cita['Servicio']}</b></p><p>Fecha: {fecha_bonita(cita['Fecha'])}</p><p>Hora: {cita['Hora']}</p>"
        f"{insignia(cita['Estado'], COLOR_ESTADO[cita['Estado']])}</div></div>",
        unsafe_allow_html=True)

    st.write("")
    if cita["Estado"] == "Pendiente":
        if st.button("Confirmar mi cita", type="primary", width="stretch"):
            cita["Estado"] = "Confirmada"
            cita["Confirmada_en"] = ahora()
            DATOS["confirmaciones"].append({"Cita": cita["ID"], "Hora": ahora()})
            bitacora(f"Cita {cita['ID']} confirmada por el cliente desde WhatsApp")
            st.rerun()
    elif cita["Estado"] == "Confirmada":
        st.success("¡Tu cita está confirmada! Te esperamos.")

    if cita["Estado"] in ("Pendiente", "Confirmada"):
        if puede_cancelar(cita):
            with st.expander("¿No puedes asistir?"):
                if st.button("Cancelar cita", width="stretch"):
                    cita["Estado"] = "Cancelada"
                    bitacora(f"Cita {cita['ID']} cancelada por el cliente desde WhatsApp")
                    st.rerun()
        else:
            st.info("Faltan menos de 48 horas para tu cita. Para cancelar o cambiarla, escríbenos.")
            st.link_button("Escribir a la clínica", width="stretch",
                           url=enlace_whatsapp(DATOS["config"]["whatsapp"],
                                               f"Hola, necesito cambiar la cita {cita['ID']} de {m['Nombre']}."))
    elif cita["Estado"] == "Cancelada":
        st.warning("Esta cita fue cancelada.")


# =====================================================================
#  VISTAS DE ADMINISTRACIÓN / RECEPCIÓN
# =====================================================================
def vista_inicio():
    usuario = st.session_state.usuario
    hora = ahora().hour
    saludo = "Buenos días" if hora < 12 else ("Buenas tardes" if hora < 19 else "Buenas noches")
    encabezado(f"{saludo}, {usuario['Nombre'].split()[0]}", fecha_bonita(hoy()))

    citas_hoy = sorted([c for c in DATOS["citas"] if c["Fecha"] == hoy()], key=lambda x: x["Hora"])
    pendientes = [c for c in DATOS["citas"] if c["Estado"] == "Pendiente" and hoy() <= c["Fecha"] <= hoy() + timedelta(days=3)]
    alertas_inv = [p for p in DATOS["productos"] if estado_producto(p) != "OK"]
    vacunas_por_vencer = [v for v in DATOS["vacunas_aplicadas"] if 0 <= (v["Proxima"] - hoy()).days <= 30]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Citas de hoy", len(citas_hoy))
    c2.metric("Por confirmar (3 días)", len(pendientes))
    c3.metric("Alertas de inventario", len(alertas_inv))
    c4.metric("Vacunas por vencer (30 días)", len(vacunas_por_vencer))

    izquierda, derecha = st.columns([3, 2], gap="large")
    with izquierda:
        st.markdown("##### Citas de hoy")
        if citas_hoy:
            for c in citas_hoy:
                tarjeta_cita(c)
        else:
            st.info("No hay citas para hoy.")
    with derecha:
        st.markdown("##### Inventario")
        if alertas_inv:
            for p in alertas_inv:
                st.markdown(f"<div class='alerta-roja'><b>{p['Nombre']}</b> · {estado_producto(p)} "
                            f"({p['Existencia']} {p['Unidad']})</div>", unsafe_allow_html=True)
        else:
            st.success("Todo en orden.")
        confirmaciones_en_vivo()


@st.fragment(run_every=10)
def confirmaciones_en_vivo():
    """Se actualiza sola cada 10 segundos para ver quién confirmó."""
    st.markdown("##### Confirmaciones en vivo")
    recientes = DATOS["confirmaciones"][-5:][::-1]
    if not recientes:
        st.caption("Aquí aparecen las citas que los clientes confirman desde WhatsApp.")
    for conf in recientes:
        cita = buscar(DATOS["citas"], conf["Cita"])
        if cita:
            st.markdown(f"<div class='tarjeta'><b>{nombre_mascota(cita['Mascota'])}</b> confirmó · "
                        f"{fecha_corta(cita['Fecha'])} {cita['Hora']}<br><span class='dato'>"
                        f"{conf['Hora'].strftime('%H:%M:%S')}</span></div>", unsafe_allow_html=True)


def vista_agenda():
    encabezado("Agenda", "Citas por día y por semana.")
    col_fecha, col_vista = st.columns([1, 2])
    fecha = col_fecha.date_input("Día", value=hoy(), format="DD/MM/YYYY")
    modo = col_vista.radio("Vista", ["Día", "Semana"], horizontal=True)

    if modo == "Día":
        citas = sorted([c for c in DATOS["citas"] if c["Fecha"] == fecha], key=lambda x: x["Hora"])
        st.markdown(f"##### {fecha_bonita(fecha)} · {len(citas)} citas")
        if fecha.weekday() == 6:
            st.info("Domingo: la clínica está cerrada.")
        for c in citas:
            col_tarjeta, col_accion = st.columns([4, 1])
            with col_tarjeta:
                tarjeta_cita(c)
            with col_accion:
                if c["Estado"] in ("Pendiente", "Confirmada"):
                    nuevo = st.selectbox("Cambiar", ESTADOS_CITA, index=ESTADOS_CITA.index(c["Estado"]),
                                         key=f"estado_{c['ID']}", label_visibility="collapsed")
                    if nuevo != c["Estado"]:
                        c["Estado"] = nuevo
                        bitacora(f"Cita {c['ID']} cambió a {nuevo}")
                        st.rerun()
        libres = horas_libres(fecha)
        if libres:
            st.caption("Horas libres: " + ", ".join(libres))
    else:
        inicio = fecha - timedelta(days=fecha.weekday())
        columnas = st.columns(6)
        for i in range(6):
            dia = inicio + timedelta(days=i)
            with columnas[i]:
                marca = "Hoy · " if dia == hoy() else ""
                st.markdown(f"**{marca}{DIAS_SEMANA[i][:3]} {dia.day}**")
                citas = sorted([c for c in DATOS["citas"] if c["Fecha"] == dia], key=lambda x: x["Hora"])
                for c in citas:
                    st.markdown(f"<div class='tarjeta' style='padding:0.4rem 0.6rem;border-left:4px solid "
                                f"{COLOR_ESTADO[c['Estado']]};'><b>{c['Hora']}</b><br>"
                                f"<span class='dato'>{nombre_mascota(c['Mascota'])}</span></div>",
                                unsafe_allow_html=True)
                if not citas:
                    st.caption("Sin citas")

    leyenda = " ".join(insignia(e, COLOR_ESTADO[e]) for e in ESTADOS_CITA)
    st.markdown(leyenda, unsafe_allow_html=True)


def vista_nueva_cita():
    encabezado("Nueva cita", "Agenda una cita para un cliente que llama o llega a la clínica.")
    if not DATOS["clientes"]:
        st.warning("Primero registra un cliente.")
        return
    opciones_cliente = {f"{c['Nombre']} · {c['Telefono']}": c["ID"] for c in DATOS["clientes"]}
    elegido = st.selectbox("Cliente", list(opciones_cliente.keys()))
    id_cliente = opciones_cliente[elegido]
    activas = [m for m in mascotas_de(id_cliente) if m["Estado"] == "Activo"]
    if not activas:
        st.warning("Este cliente no tiene mascotas activas. Regístrala en 'Mascotas'.")
        return

    opciones_mascota = {f"{m['Nombre']} ({m['Especie']})": m["ID"] for m in activas}
    col1, col2 = st.columns(2)
    nombre_m = col1.selectbox("Mascota", list(opciones_mascota.keys()))
    servicio = col2.selectbox("Servicio", SERVICIOS)
    fecha = col1.date_input("Fecha", value=hoy(), min_value=hoy(), format="DD/MM/YYYY")
    libres = horas_libres(fecha)
    if not libres:
        st.warning("No hay horarios libres ese día (domingo cerrado o agenda llena).")
        return
    hora = col2.selectbox("Hora", libres)
    notas = st.text_area("Notas (opcional)")
    if st.button("Agendar cita", type="primary"):
        cita = crear_cita(opciones_mascota[nombre_m], servicio, fecha, hora, notas)
        st.success(f"Cita {cita['ID']} agendada. Quedó como Pendiente hasta que el cliente confirme.")


def vista_confirmaciones():
    encabezado("Confirmar citas por WhatsApp",
               "Envía el recordatorio con un enlace; cuando el cliente confirma, la cita cambia sola.")
    if not url_de_la_app():
        st.warning("Configura la URL pública en Ajustes para que el enlace funcione.")
    dias = st.slider("Mostrar citas de los próximos días", 1, 14, 3)
    izquierda, derecha = st.columns([3, 2], gap="large")
    with izquierda:
        lista_por_confirmar(dias)
    with derecha:
        confirmaciones_en_vivo()


@st.fragment(run_every=10)
def lista_por_confirmar(dias):
    """Lista de citas pendientes; se refresca sola para quitar las que ya confirmaron."""
    pendientes = sorted([c for c in DATOS["citas"] if c["Estado"] == "Pendiente"
                         and hoy() <= c["Fecha"] <= hoy() + timedelta(days=dias)],
                        key=lambda x: (x["Fecha"], x["Hora"]))
    st.markdown(f"##### {len(pendientes)} citas por confirmar")
    for c in pendientes:
        tarjeta_cita(c)
        cli = cliente(c["Cliente"])
        st.link_button(f"Enviar recordatorio a {cli['Nombre'].split()[0]}",
                       enlace_whatsapp(cli["Telefono"], mensaje_recordatorio(c)))
    if not pendientes:
        st.success("No hay citas pendientes de confirmar.")


def vista_clientes():
    encabezado("Clientes", "Dueños registrados en la clínica.")
    tab_lista, tab_nuevo = st.tabs(["Lista", "Nuevo cliente"])
    with tab_lista:
        texto = st.text_input("Buscar por nombre o teléfono")
        filas = []
        for c in DATOS["clientes"]:
            if texto.lower() in c["Nombre"].lower() or texto in c["Telefono"]:
                citas = [ct for ct in DATOS["citas"] if ct["Cliente"] == c["ID"]]
                ultima = max([ct["Fecha"] for ct in citas if ct["Estado"] == "Completada"], default=None)
                filas.append({"ID": c["ID"], "Nombre": c["Nombre"], "Teléfono": c["Telefono"],
                              "Correo": c["Correo"], "Mascotas": len(mascotas_de(c["ID"])),
                              "Citas": len(citas), "Última visita": ultima})
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    with tab_nuevo:
        with st.form("nuevo_cliente", clear_on_submit=True):
            nombre = st.text_input("Nombre completo")
            telefono = st.text_input("Teléfono (10 dígitos)", max_chars=10)
            correo = st.text_input("Correo")
            guardar_btn = st.form_submit_button("Guardar cliente", type="primary")
        if guardar_btn:
            if not nombre.strip() or not (telefono.isdigit() and len(telefono) == 10):
                st.error("Escribe el nombre y un teléfono de 10 dígitos.")
            elif any(c["Telefono"] == telefono for c in DATOS["clientes"]):
                st.error("Ya existe un cliente con ese teléfono.")
            else:
                nuevo = {"ID": nuevo_id(DATOS["clientes"], "C"), "Nombre": nombre.strip(), "Telefono": telefono,
                         "Correo": correo.strip(), "Contrasena": telefono[-4:], "Alta": hoy()}
                DATOS["clientes"].append(nuevo)
                bitacora(f"Cliente {nuevo['Nombre']} registrado en recepción")
                st.success(f"Cliente guardado. Puede entrar a la app con su teléfono y la contraseña "
                           f"**{telefono[-4:]}** (últimos 4 dígitos).")


def formulario_mascota(id_cliente, clave):
    """Formulario para registrar una mascota (lo usan recepción y el cliente)."""
    with st.form(clave, clear_on_submit=True):
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre")
        especie = col2.selectbox("Especie", ESPECIES)
        raza = col1.text_input("Raza")
        sexo = col2.selectbox("Sexo", ["Macho", "Hembra"])
        edad = col1.number_input("Edad (años)", 0, 40, 1)
        peso = col2.number_input("Peso (kg)", 0.0, 120.0, 5.0, step=0.1)
        tamano = col1.selectbox("Tamaño", TAMANOS)
        alergias = col2.text_input("Alergias (si tiene)")
        foto = st.file_uploader("Foto", type=["jpg", "jpeg", "png"])
        enviar = st.form_submit_button("Guardar mascota", type="primary")
    if enviar:
        if not nombre.strip():
            st.error("Escribe el nombre de la mascota.")
            return
        nueva = {"ID": nuevo_id(DATOS["mascotas"], "M"), "Nombre": nombre.strip(), "Especie": especie,
                 "Raza": raza.strip() or "Sin especificar", "Sexo": sexo, "Edad": int(edad),
                 "Peso": round(peso, 2), "Tamano": tamano, "Cliente": id_cliente, "Estado": "Activo",
                 "Alergias": alergias.strip(), "Foto": preparar_foto(foto) if foto else None, "Alta": hoy()}
        DATOS["mascotas"].append(nueva)
        bitacora(f"Mascota {nueva['Nombre']} ({nueva['ID']}) registrada")
        st.success(f"¡{nueva['Nombre']} quedó registrada!")


def vista_mascotas():
    encabezado("Mascotas", "Pacientes de la clínica, con foto y estado.")
    tab_lista, tab_nueva, tab_editar = st.tabs(["Pacientes", "Nueva mascota", "Editar / estado"])

    with tab_lista:
        col1, col2, col3 = st.columns(3)
        texto = col1.text_input("Buscar por nombre")
        especie = col2.selectbox("Especie", ["Todas"] + ESPECIES)
        estado = col3.selectbox("Estado", ["Todos"] + ESTADOS_MASCOTA)
        lista = [m for m in DATOS["mascotas"]
                 if texto.lower() in m["Nombre"].lower()
                 and (especie == "Todas" or m["Especie"] == especie)
                 and (estado == "Todos" or m["Estado"] == estado)]
        st.caption(f"{len(lista)} mascotas")
        columnas = st.columns(5)
        for i, m in enumerate(lista):
            with columnas[i % 5]:
                st.markdown(
                    f"<div class='tarjeta'>{foto_html(m)}<p style='margin:0.5rem 0 0 0;'><b>{m['Nombre']}</b> "
                    f"<span class='dato'>{m['ID']}</span></p><p class='dato'>{m['Especie']} · "
                    f"{nombre_cliente(m['Cliente'])}</p>{insignia(m['Estado'], COLOR_MASCOTA[m['Estado']])}</div>",
                    unsafe_allow_html=True)

    with tab_nueva:
        opciones = {f"{c['Nombre']} · {c['Telefono']}": c["ID"] for c in DATOS["clientes"]}
        dueno = st.selectbox("Dueño", list(opciones.keys()))
        formulario_mascota(opciones[dueno], "mascota_recepcion")

    with tab_editar:
        opciones = {f"{m['Nombre']} · {m['ID']} · {nombre_cliente(m['Cliente'])}": m["ID"] for m in DATOS["mascotas"]}
        elegida = mascota(opciones[st.selectbox("Mascota", list(opciones.keys()))])
        with st.form("editar_mascota"):
            col1, col2 = st.columns(2)
            peso = col1.number_input("Peso (kg)", 0.0, 120.0, float(elegida["Peso"]), step=0.1)
            edad = col2.number_input("Edad (años)", 0, 40, int(elegida["Edad"]))
            alergias = col1.text_input("Alergias", value=elegida["Alergias"])
            estado = col2.selectbox("Estado", ESTADOS_MASCOTA, index=ESTADOS_MASCOTA.index(elegida["Estado"]))
            foto = st.file_uploader("Cambiar foto", type=["jpg", "jpeg", "png"])
            listo = st.form_submit_button("Guardar cambios", type="primary")
        if listo:
            elegida["Peso"], elegida["Edad"], elegida["Alergias"] = round(peso, 2), int(edad), alergias.strip()
            if foto:
                elegida["Foto"] = preparar_foto(foto)
            if estado != elegida["Estado"]:
                elegida["Estado"] = estado
                if estado == "Fallecido":
                    # Se cancelan sus citas futuras
                    for c in DATOS["citas"]:
                        if c["Mascota"] == elegida["ID"] and c["Estado"] in ("Pendiente", "Confirmada"):
                            c["Estado"] = "Cancelada"
            bitacora(f"Mascota {elegida['Nombre']} actualizada (estado: {elegida['Estado']})")
            st.success("Cambios guardados.")


def vista_expediente():
    encabezado("Expediente clínico", "Historial completo de cada paciente.")
    opciones = {f"{m['Nombre']} · {m['ID']} · {nombre_cliente(m['Cliente'])}": m["ID"] for m in DATOS["mascotas"]}
    m = mascota(opciones[st.selectbox("Paciente", list(opciones.keys()))])
    carnet_mascota(m)

    st.markdown("##### Consultas")
    consultas = sorted([c for c in DATOS["consultas"] if c["Mascota"] == m["ID"]], key=lambda x: x["Fecha"], reverse=True)
    if consultas:
        tabla = pd.DataFrame(consultas)[["Fecha", "Motivo", "Peso", "Temperatura", "Diagnostico",
                                         "Tratamiento", "Medicamento", "Veterinario"]]
        st.dataframe(tabla, hide_index=True, width="stretch")
        if len(consultas) > 1:
            figura = px.line(pd.DataFrame(consultas).sort_values("Fecha"), x="Fecha", y="Peso",
                             markers=True, title="Evolución del peso (kg)", color_discrete_sequence=["#2F8CEB"])
            figura.update_traces(line_width=2, marker_size=8)
            st.plotly_chart(estilo_grafica(figura, 280), width="stretch")
    else:
        st.info("Sin consultas registradas.")

    st.markdown("##### Citas")
    citas = sorted([c for c in DATOS["citas"] if c["Mascota"] == m["ID"]], key=lambda x: x["Fecha"], reverse=True)
    if citas:
        st.dataframe(tabla_citas(citas), hide_index=True, width="stretch")


def vista_inventario():
    es_admin = st.session_state.usuario["Tipo"] == "Administrador"  # solo el administrador registra entradas
    encabezado("Inventario", "Medicamentos y material con existencias, caducidad y alertas.")
    tabs = ["Existencias", "Sugerencia de compra", "Movimientos"]
    if es_admin:
        tabs += ["Entrada / producto nuevo"]
    pestanas = st.tabs(tabs)

    with pestanas[0]:
        filas = []
        for p in DATOS["productos"]:
            dias = (p["Caducidad"] - hoy()).days
            filas.append({"ID": p["ID"], "Producto": p["Nombre"], "Categoría": p["Categoria"],
                          "Existencia": p["Existencia"], "Mínimo": p["Minimo"], "Unidad": p["Unidad"],
                          "Caduca": p["Caducidad"], "Días para caducar": dias, "Estado": estado_producto(p)})
        tabla = pd.DataFrame(filas)
        problemas = tabla[tabla["Estado"] != "OK"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Productos", len(tabla))
        c2.metric("Con alerta", len(problemas))
        c3.metric("Por caducar (30 días)", int((tabla["Estado"] == "Por caducar").sum()))
        st.dataframe(tabla, hide_index=True, width="stretch",
                     column_config={"Existencia": st.column_config.ProgressColumn(
                         "Existencia", format="%d", min_value=0, max_value=int(tabla["Existencia"].max() or 1))})

    with pestanas[1]:
        st.caption("Cálculo: consumo promedio de los últimos 90 días × 1.5 meses de cobertura − existencia actual.")
        filas = []
        for p in DATOS["productos"]:
            consumo = consumo_mensual(p["Nombre"])
            necesario = max(consumo * 1.5, p["Minimo"] * 1.5)
            sugerido = max(0, math.ceil(necesario - p["Existencia"]))
            if sugerido > 0:
                filas.append({"Producto": p["Nombre"], "Existencia": p["Existencia"],
                              "Consumo mensual": round(consumo, 1), "Comprar": sugerido, "Unidad": p["Unidad"]})
        if filas:
            st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        else:
            st.success("No hace falta comprar nada por ahora.")

    with pestanas[2]:
        movimientos = sorted(DATOS["movimientos"], key=lambda x: x["Fecha"], reverse=True)
        st.dataframe(pd.DataFrame(movimientos), hide_index=True, width="stretch")

    if es_admin:
        with pestanas[3]:
            st.markdown("###### Registrar entrada (compra)")
            with st.form("entrada", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                nombre = col1.selectbox("Producto", [p["Nombre"] for p in DATOS["productos"]])
                cantidad = col2.number_input("Cantidad", 1, 1000, 10)
                caducidad = col3.date_input("Nueva caducidad", value=hoy() + timedelta(days=365), format="DD/MM/YYYY")
                ok = st.form_submit_button("Registrar entrada", type="primary")
            if ok:
                p = producto_por_nombre(nombre)
                p["Existencia"] += int(cantidad)
                p["Caducidad"] = caducidad
                DATOS["movimientos"].append({"Fecha": hoy(), "Producto": nombre, "Tipo": "Entrada",
                                             "Cantidad": int(cantidad), "Motivo": "Compra a proveedor"})
                bitacora(f"Entrada de {cantidad} {p['Unidad']} de {nombre}")
                st.success("Entrada registrada.")

            st.markdown("###### Producto nuevo")
            with st.form("producto_nuevo", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                nombre = col1.text_input("Nombre")
                categoria = col2.selectbox("Categoría", ["Vacuna", "Desparasitante", "Antibiótico",
                                                         "Antiinflamatorio", "Material", "Estética", "Otro"])
                unidad = col3.text_input("Unidad", value="pieza")
                existencia = col1.number_input("Existencia inicial", 0, 5000, 10)
                minimo = col2.number_input("Mínimo", 0, 1000, 5)
                caducidad = col3.date_input("Caducidad", value=hoy() + timedelta(days=365), format="DD/MM/YYYY",
                                            key="cad_nuevo")
                ok = st.form_submit_button("Agregar producto", type="primary")
            if ok:
                if not nombre.strip() or producto_por_nombre(nombre.strip()):
                    st.error("Escribe un nombre que no exista ya.")
                else:
                    DATOS["productos"].append({"ID": nuevo_id(DATOS["productos"], "P"), "Nombre": nombre.strip(),
                                               "Categoria": categoria, "Unidad": unidad, "Existencia": int(existencia),
                                               "Minimo": int(minimo), "Caducidad": caducidad})
                    bitacora(f"Producto nuevo: {nombre.strip()}")
                    st.success("Producto agregado.")


def vista_tablero():
    encabezado("Tablero de indicadores (BI)", "Asistencia, cancelación, retención y demanda de la clínica.")
    periodo = st.pills("Periodo", ["30 días", "90 días", "180 días"], default="90 días")
    dias = int((periodo or "90 días").split()[0])
    desde = hoy() - timedelta(days=dias)
    citas = [c for c in DATOS["citas"] if desde <= c["Fecha"] < hoy()]
    if not citas:
        st.info("No hay citas en ese periodo.")
        return
    df = tabla_citas(citas)
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    df["Hora"] = df["Hora"].str[:2] + ":00"

    completadas = (df["Estado"] == "Completada").sum()
    no_asistio = (df["Estado"] == "No asistió").sum()
    canceladas = (df["Estado"] == "Cancelada").sum()
    asistencia = completadas / max(completadas + no_asistio, 1) * 100
    cancelacion = canceladas / len(df) * 100

    # Pacientes distintos que sí vinieron en el periodo
    atendidos = df[df["Estado"] == "Completada"]["Mascota"].nunique()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Citas en el periodo", len(df))
    c2.metric("Tasa de asistencia", f"{asistencia:.0f}%")
    c3.metric("Tasa de cancelación", f"{cancelacion:.0f}%")
    c4.metric("Pacientes atendidos", atendidos)

    col1, col2 = st.columns(2)
    with col1:
        por_semana = df.set_index("Fecha").resample("W-MON").size().reset_index(name="Citas")
        figura = px.bar(por_semana, x="Fecha", y="Citas", title="Citas por semana",
                        color_discrete_sequence=["#2F8CEB"])
        st.plotly_chart(estilo_grafica(figura), width="stretch")
    with col2:
        estados = df["Estado"].value_counts().reindex(ESTADOS_CITA).dropna().reset_index()
        estados.columns = ["Estado", "Citas"]
        figura = px.bar(estados, x="Estado", y="Citas", title="Citas por estado",
                        color="Estado", color_discrete_map=COLOR_ESTADO)
        st.plotly_chart(estilo_grafica(figura), width="stretch")

    col3, col4 = st.columns(2)
    with col3:
        horas = df.groupby("Hora").size().reset_index(name="Citas")
        figura = px.bar(horas, x="Hora", y="Citas", title="Demanda por horario",
                        color_discrete_sequence=["#2F8CEB"])
        st.plotly_chart(estilo_grafica(figura), width="stretch")
    with col4:
        servicios = df["Servicio"].value_counts().sort_values().reset_index()
        servicios.columns = ["Servicio", "Citas"]
        figura = px.bar(servicios, x="Citas", y="Servicio", orientation="h", title="Servicios más pedidos",
                        color_discrete_sequence=["#2F8CEB"])
        st.plotly_chart(estilo_grafica(figura), width="stretch")

    st.markdown("##### Clientes inactivos (más de 90 días sin venir)")
    filas = []
    for c in DATOS["clientes"]:
        visitas_cliente = [ct["Fecha"] for ct in DATOS["citas"] if ct["Cliente"] == c["ID"] and ct["Estado"] == "Completada"]
        futuras = [ct for ct in DATOS["citas"] if ct["Cliente"] == c["ID"] and ct["Fecha"] >= hoy()
                   and ct["Estado"] in ("Pendiente", "Confirmada")]
        if visitas_cliente and not futuras:
            ultima = max(visitas_cliente)
            if (hoy() - ultima).days > 90:
                filas.append({"Cliente": c["Nombre"], "Teléfono": c["Telefono"], "Última visita": ultima,
                              "Días sin venir": (hoy() - ultima).days})
    if filas:
        st.dataframe(pd.DataFrame(filas).sort_values("Días sin venir", ascending=False), hide_index=True, width="stretch")
    else:
        st.success("Todos los clientes han venido en los últimos 90 días o ya tienen cita.")


def vista_reportes():
    encabezado("Reportes", "Descarga la información en CSV para Excel o Power BI.")
    tablas = {
        "Clientes": [{k: v for k, v in c.items() if k != "Contrasena"} for c in DATOS["clientes"]],
        "Mascotas": [{k: v for k, v in m.items() if k != "Foto"} for m in DATOS["mascotas"]],
        "Citas": DATOS["citas"],
        "Consultas": DATOS["consultas"],
        "Vacunas aplicadas": DATOS["vacunas_aplicadas"],
        "Inventario": DATOS["productos"],
        "Movimientos de inventario": DATOS["movimientos"],
        "Bitácora": DATOS["auditoria"],
    }
    columnas = st.columns(4)
    for i, (nombre, datos) in enumerate(tablas.items()):
        with columnas[i % 4]:
            csv = pd.DataFrame(datos).to_csv(index=False).encode("utf-8-sig")  # utf-8-sig = acentos bien en Excel
            st.markdown(f"<div class='tarjeta'><b>{nombre}</b><br><span class='dato'>{len(datos)} registros</span></div>",
                        unsafe_allow_html=True)
            st.download_button("Descargar", csv, file_name=f"{nombre.lower().replace(' ', '_')}.csv",
                               mime="text/csv", key=f"csv_{i}", width="stretch")

    st.markdown("##### Vacunas por vencer en los próximos 30 días")
    filas = []
    for v in DATOS["vacunas_aplicadas"]:
        dias = (v["Proxima"] - hoy()).days
        m = mascota(v["Mascota"])
        if 0 <= dias <= 30 and m["Estado"] == "Activo":
            c = cliente(m["Cliente"])
            filas.append({"Mascota": m["Nombre"], "Dueño": c["Nombre"], "Teléfono": c["Telefono"],
                          "Vacuna": v["Vacuna"], "Vence": v["Proxima"], "Días": dias})
    if filas:
        st.dataframe(pd.DataFrame(filas).sort_values("Días"), hide_index=True, width="stretch")
    else:
        st.info("No hay vacunas por vencer.")


def vista_personal():
    encabezado("Personal", "Usuarios de la clínica (administración y veterinarios).")
    tabla = pd.DataFrame([{k: v for k, v in u.items() if k != "Contrasena"} for u in DATOS["usuarios"]])
    st.dataframe(tabla, hide_index=True, width="stretch")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("###### Agregar usuario")
        with st.form("nuevo_usuario", clear_on_submit=True):
            nombre = st.text_input("Nombre")
            usuario = st.text_input("Usuario")
            contrasena = st.text_input("Contraseña", type="password")
            rol = st.selectbox("Rol", ["Recepción", "Veterinario", "Administrador"])
            ok = st.form_submit_button("Agregar", type="primary")
        if ok:
            usuario = usuario.strip().lower()
            if not nombre or not usuario or len(contrasena) < 4:
                st.error("Completa todos los datos (contraseña de 4 caracteres o más).")
            elif any(u["Usuario"] == usuario for u in DATOS["usuarios"]):
                st.error("Ese usuario ya existe.")
            else:
                DATOS["usuarios"].append({"Usuario": usuario, "Contrasena": contrasena, "Nombre": nombre.strip(),
                                          "Rol": rol, "Activo": True})
                bitacora(f"Usuario {usuario} ({rol}) creado")
                st.rerun()
    with col2:
        st.markdown("###### Activar / desactivar")
        otros = [u["Usuario"] for u in DATOS["usuarios"] if u["Usuario"] != st.session_state.usuario.get("Usuario")]
        if otros:
            elegido = st.selectbox("Usuario", otros)
            u = [x for x in DATOS["usuarios"] if x["Usuario"] == elegido][0]
            texto = "Desactivar" if u["Activo"] else "Activar"
            if st.button(f"{texto} a {elegido}"):
                u["Activo"] = not u["Activo"]
                bitacora(f"Usuario {elegido} {'activado' if u['Activo'] else 'desactivado'}")
                st.rerun()


def vista_gafete():
    encabezado("Gafete digital", "Identificación del personal.")
    u = [x for x in DATOS["usuarios"] if x["Usuario"] == st.session_state.usuario.get("Usuario")][0]
    atendidas = len([c for c in DATOS["consultas"] if c["Veterinario"] == u["Nombre"]])
    _, centro, _ = st.columns([1, 2, 1])
    with centro:
        st.markdown(
            f"""
            <div style='background:#FFFFFF;border:1px solid #DCEAF8;border-radius:20px;overflow:hidden;
                        box-shadow:0 8px 24px rgba(18,48,77,0.08);'>
                <div style='background:linear-gradient(135deg,#2F8CEB,#5AAAF8);padding:1.2rem;text-align:center;'>
                    <p style='margin:0;color:#FFFFFF;font-weight:800;letter-spacing:0.1em;'>{DATOS['config']['clinica'].upper()}</p>
                    <p style='margin:0;color:#EAF4FF;font-size:0.85rem;'>Identificación del personal</p>
                </div>
                <div style='padding:1.8rem;text-align:center;'>
                    <div style='width:92px;height:92px;border-radius:50%;background:#EAF4FF;border:3px solid #2F8CEB;
                                margin:0 auto 0.8rem auto;display:flex;align-items:center;justify-content:center;
                                font-size:2.4rem;font-weight:800;color:#1663B8;'>{u['Nombre'][0]}</div>
                    <h2 style='margin:0;'>{u['Nombre']}</h2>
                    <p class='dato'>@{u['Usuario']}</p>
                    <p style='margin-top:0.8rem;'>{insignia(u['Rol'], '#2F8CEB')}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if u["Rol"] == "Veterinario":
            st.metric("Consultas atendidas", atendidas)


def vista_bitacora():
    encabezado("Bitácora de auditoría", "Quién hizo qué y cuándo.")
    df = pd.DataFrame(DATOS["auditoria"][::-1])
    texto = st.text_input("Filtrar")
    if texto:
        df = df[df["Acción"].str.contains(texto, case=False) | df["Usuario"].str.contains(texto, case=False)]
    st.dataframe(df, hide_index=True, width="stretch")
    st.caption(f"{len(df)} eventos")


def vista_ajustes():
    encabezado("Ajustes", "Datos de la clínica y enlace público.")
    config = DATOS["config"]
    with st.form("ajustes"):
        clinica = st.text_input("Nombre de la clínica", value=config["clinica"])
        whatsapp = st.text_input("WhatsApp de la clínica (10 dígitos)", value=config["whatsapp"])
        url = st.text_input("URL pública (déjala vacía en Streamlit Cloud: se detecta sola)", value=config["url_publica"])
        ok = st.form_submit_button("Guardar", type="primary")
    if ok:
        config["clinica"], config["whatsapp"], config["url_publica"] = clinica.strip(), whatsapp.strip(), url.strip()
        bitacora("Ajustes de la clínica actualizados")
        st.success("Guardado.")
    st.caption(f"Enlace que se manda por WhatsApp: {url_de_la_app()}/?cita=...")

    st.markdown("##### Reiniciar demostración")
    st.caption("Borra todo lo capturado y vuelve a cargar los datos de ejemplo.")
    if st.button("Restablecer datos de ejemplo"):
        nuevos = crear_datos_ejemplo()
        DATOS.clear()
        DATOS.update(nuevos)
        guardar()
        st.success("Datos restablecidos.")


# =====================================================================
#  VISTAS DEL VETERINARIO
# =====================================================================
def vista_agenda_vet():
    encabezado(f"Mi agenda · {fecha_bonita(hoy())}", "Pacientes del día. Toca 'Atender' para registrar la consulta.")
    citas = sorted([c for c in DATOS["citas"] if c["Fecha"] == hoy()], key=lambda x: x["Hora"])
    por_atender = [c for c in citas if c["Estado"] in ("Pendiente", "Confirmada")]
    c1, c2, c3 = st.columns(3)
    c1.metric("Citas de hoy", len(citas))
    c2.metric("Por atender", len(por_atender))
    c3.metric("Atendidas", len([c for c in citas if c["Estado"] == "Completada"]))

    if "atendiendo" in st.session_state:
        formulario_consulta(st.session_state.atendiendo)
        return

    for c in citas:
        col_tarjeta, col_boton = st.columns([4, 1])
        with col_tarjeta:
            tarjeta_cita(c)
            m = mascota(c["Mascota"])
            if m["Alergias"]:
                st.markdown(f"<div class='alerta-roja'>Alergia: {m['Alergias']}</div>", unsafe_allow_html=True)
        with col_boton:
            if c["Estado"] in ("Pendiente", "Confirmada"):
                if st.button("Atender", key=f"atender_{c['ID']}", type="primary", width="stretch"):
                    st.session_state.atendiendo = c["ID"]
                    st.rerun()
                if st.button("No asistió", key=f"falta_{c['ID']}", width="stretch"):
                    c["Estado"] = "No asistió"
                    bitacora(f"Cita {c['ID']} marcada como No asistió")
                    st.rerun()
    if not citas:
        st.info("No hay citas hoy.")

    proximas = sorted([c for c in DATOS["citas"] if hoy() < c["Fecha"] <= hoy() + timedelta(days=3)
                       and c["Estado"] in ("Pendiente", "Confirmada")], key=lambda x: (x["Fecha"], x["Hora"]))
    if proximas:
        st.markdown("##### Próximos 3 días")
        st.dataframe(tabla_citas(proximas), hide_index=True, width="stretch")


def formulario_consulta(id_cita):
    cita = buscar(DATOS["citas"], id_cita)
    m = mascota(cita["Mascota"])
    st.markdown(f"#### Consulta de {m['Nombre']} · {cita['Servicio']}")
    if m["Alergias"]:
        st.markdown(f"<div class='alerta-roja'>Alergia: <b>{m['Alergias']}</b></div>", unsafe_allow_html=True)

    medicamentos = ["(ninguno)"] + [p["Nombre"] for p in DATOS["productos"]
                                    if p["Categoria"] != "Vacuna" and p["Existencia"] > 0]
    with st.form("consulta"):
        col1, col2 = st.columns(2)
        peso = col1.number_input("Peso (kg)", 0.0, 120.0, float(m["Peso"]), step=0.1)
        temperatura = col2.number_input("Temperatura (°C)", 30.0, 45.0, 38.5, step=0.1)
        diagnostico = st.text_input("Diagnóstico")
        tratamiento = st.text_area("Tratamiento / indicaciones")
        col3, col4 = st.columns(2)
        vacuna = col3.selectbox("Vacuna aplicada", ["(ninguna)"] + list(VACUNAS.keys()))
        desparasitar = col4.checkbox("Se desparasitó (descuenta 1 tableta)")
        medicamento = col3.selectbox("Medicamento del inventario", medicamentos)
        cantidad = col4.number_input("Cantidad", 0, 100, 0)
        col_guardar, col_cancelar = st.columns(2)
        guardar_btn = col_guardar.form_submit_button("Guardar consulta", type="primary", width="stretch")
        cancelar = col_cancelar.form_submit_button("Volver", width="stretch")

    if cancelar:
        del st.session_state.atendiendo
        st.rerun()
    if guardar_btn:
        if not diagnostico.strip():
            st.error("Escribe el diagnóstico.")
            return
        avisos = []
        if vacuna != "(ninguna)":
            if descontar_producto(VACUNAS[vacuna]["producto"], 1, f"Vacuna a {m['Nombre']}"):
                DATOS["vacunas_aplicadas"].append({"Mascota": m["ID"], "Vacuna": vacuna, "Fecha": hoy(),
                                                   "Proxima": hoy() + timedelta(days=VACUNAS[vacuna]["dias"])})
            else:
                avisos.append(f"No hay existencia de {VACUNAS[vacuna]['producto']}; la vacuna no se registró.")
        if desparasitar and not descontar_producto("Desparasitante oral (tableta)", 1, f"Desparasitación de {m['Nombre']}"):
            avisos.append("No hay desparasitante en inventario.")
        if medicamento != "(ninguno)" and cantidad > 0:
            if not descontar_producto(medicamento, int(cantidad), f"Receta para {m['Nombre']}"):
                avisos.append(f"No alcanza la existencia de {medicamento}.")
                medicamento, cantidad = "", 0
        else:
            medicamento, cantidad = "", 0

        DATOS["consultas"].append({
            "ID": nuevo_id(DATOS["consultas"], "CO", 4), "Cita": cita["ID"], "Mascota": m["ID"], "Fecha": hoy(),
            "Veterinario": st.session_state.usuario["Nombre"], "Motivo": cita["Servicio"], "Peso": round(peso, 2),
            "Temperatura": temperatura, "Diagnostico": diagnostico.strip(), "Tratamiento": tratamiento.strip(),
            "Medicamento": medicamento, "Cantidad": int(cantidad),
        })
        m["Peso"] = round(peso, 2)
        cita["Estado"] = "Completada"
        bitacora(f"Consulta de {m['Nombre']} registrada (cita {cita['ID']})")
        del st.session_state.atendiendo
        st.session_state.aviso_consulta = avisos
        st.rerun()


# =====================================================================
#  APP DEL CLIENTE (CELULAR)
# =====================================================================
def portal_cliente():
    st.markdown(CSS_MOVIL, unsafe_allow_html=True)
    usuario = st.session_state.usuario
    yo = cliente(usuario["ID"])
    st.markdown(f"<p style='font-weight:800;font-size:1.3rem;color:#1663B8;margin:0;'>{DATOS['config']['clinica']}</p>"
                f"<p class='dato'>Hola, {yo['Nombre'].split()[0]}</p>", unsafe_allow_html=True)

    seccion = st.pills("Menú", ["Mis mascotas", "Agendar", "Mis citas", "Carnet", "Salir"],
                       default="Mis mascotas", label_visibility="collapsed")
    seccion = seccion or "Mis mascotas"
    mis_mascotas = [m for m in mascotas_de(yo["ID"]) if m["Estado"] != "Fallecido"]

    if seccion == "Salir":
        bitacora(f"Cliente {yo['Nombre']} salió")
        del st.session_state.usuario
        st.rerun()

    if seccion == "Mis mascotas":
        for m in mis_mascotas:
            st.markdown(
                f"<div class='tarjeta fila-mascota'>{foto_html(m, 92)}<div><b style='font-size:1.1rem;'>"
                f"{m['Nombre']}</b><p class='dato'>{m['Especie']} · {m['Raza']}</p><p class='dato'>"
                f"{m['Peso']} kg · {m['Tamano']} · {m['Edad']} años</p>"
                f"{insignia(m['Estado'], COLOR_MASCOTA[m['Estado']])}</div></div>",
                unsafe_allow_html=True)
        if not mis_mascotas:
            st.info("Aún no registras mascotas. ¡Agrega la primera!")
        with st.expander("Registrar una mascota", expanded=not mis_mascotas):
            st.caption("El veterinario completará su expediente en la primera visita.")
            formulario_mascota(yo["ID"], "mascota_cliente")

    elif seccion == "Agendar":
        activas = [m for m in mis_mascotas if m["Estado"] == "Activo"]
        if not activas:
            st.info("Primero registra una mascota.")
            return
        st.markdown("**¿Para quién es la cita?**")
        id_mascota = selector_mascota(activas, "mascota_cita")
        servicio = st.selectbox("Servicio", SERVICIOS)
        fecha = st.date_input("Fecha", value=hoy() + timedelta(days=1), min_value=hoy(), format="DD/MM/YYYY")
        libres = horas_libres(fecha)
        if not libres:
            st.warning("No hay horarios ese día. Elige otra fecha (domingo cerrado).")
            return
        hora = st.pills("Hora", libres)
        if st.button("Agendar cita", type="primary", width="stretch", disabled=hora is None):
            cita = crear_cita(id_mascota, servicio, fecha, hora)
            st.success(f"¡Listo! Cita para {nombre_mascota(id_mascota)} el {fecha_bonita(fecha)} a las {hora}. "
                       f"La clínica te enviará un WhatsApp para confirmarla.")
            st.balloons()

    elif seccion == "Mis citas":
        citas = sorted([c for c in DATOS["citas"] if c["Cliente"] == yo["ID"] and c["Fecha"] >= hoy()],
                       key=lambda x: (x["Fecha"], x["Hora"]))
        if not citas:
            st.info("No tienes citas próximas.")
        for c in citas:
            tarjeta_cita(c, mostrar_dueno=False)
            if c["Estado"] == "Pendiente":
                if st.button("Confirmar", key=f"conf_{c['ID']}", width="stretch"):
                    c["Estado"] = "Confirmada"
                    c["Confirmada_en"] = ahora()
                    DATOS["confirmaciones"].append({"Cita": c["ID"], "Hora": ahora()})
                    bitacora(f"Cita {c['ID']} confirmada por el cliente desde la app")
                    st.rerun()
            if c["Estado"] in ("Pendiente", "Confirmada"):
                if puede_cancelar(c):
                    if st.button("Cancelar cita", key=f"canc_{c['ID']}", width="stretch"):
                        c["Estado"] = "Cancelada"
                        bitacora(f"Cita {c['ID']} cancelada por el cliente desde la app")
                        st.rerun()
                else:
                    st.caption("Faltan menos de 48 h: para cancelar escribe a la clínica.")
                    st.link_button("Escribir por WhatsApp", width="stretch", url=enlace_whatsapp(
                        DATOS["config"]["whatsapp"], f"Hola, soy {yo['Nombre']}. Necesito cambiar la cita {c['ID']} "
                                                     f"de {nombre_mascota(c['Mascota'])}."))
            st.write("")

    elif seccion == "Carnet":
        if not mis_mascotas:
            st.info("Primero registra una mascota.")
            return
        id_mascota = selector_mascota(mis_mascotas, "mascota_carnet")
        carnet_mascota(mascota(id_mascota))


# =====================================================================
#  MENÚ Y PROGRAMA PRINCIPAL
# =====================================================================
# El ADMINISTRADOR ve todo: es el único que puede ver el tablero BI,
# descargar reportes, dar de alta personal, ver la bitácora, cambiar
# ajustes y registrar compras de inventario.
MENU_ADMIN = {
    "Inicio": vista_inicio,
    "Agenda": vista_agenda,
    "Nueva cita": vista_nueva_cita,
    "Confirmar por WhatsApp": vista_confirmaciones,
    "Clientes": vista_clientes,
    "Mascotas": vista_mascotas,
    "Expedientes": vista_expediente,
    "Inventario": vista_inventario,
    "Tablero BI": vista_tablero,
    "Reportes": vista_reportes,
    "Personal": vista_personal,
    "Gafete digital": vista_gafete,
    "Bitácora": vista_bitacora,
    "Ajustes": vista_ajustes,
}

# RECEPCIÓN se encarga del día a día: citas, WhatsApp, clientes y mascotas.
# El inventario solo lo puede consultar.
MENU_RECEPCION = {
    "Inicio": vista_inicio,
    "Agenda": vista_agenda,
    "Nueva cita": vista_nueva_cita,
    "Confirmar por WhatsApp": vista_confirmaciones,
    "Clientes": vista_clientes,
    "Mascotas": vista_mascotas,
    "Expedientes": vista_expediente,
    "Inventario": vista_inventario,
    "Gafete digital": vista_gafete,
}

# El VETERINARIO atiende consultas y revisa expedientes.
MENU_VET = {
    "Mi agenda": vista_agenda_vet,
    "Expedientes": vista_expediente,
    "Mascotas": vista_mascotas,
    "Inventario": vista_inventario,
    "Gafete digital": vista_gafete,
}


def panel_personal():
    usuario = st.session_state.usuario
    if usuario["Tipo"] == "Administrador":
        menu = MENU_ADMIN
    elif usuario["Tipo"] == "Recepción":
        menu = MENU_RECEPCION
    else:
        menu = MENU_VET
    with st.sidebar:
        st.markdown(f"<p style='font-weight:800;font-size:1.4rem;color:#1663B8;margin:0;'>VetSmart</p>"
                    f"<p class='dato'>{DATOS['config']['clinica']}</p>", unsafe_allow_html=True)
        st.markdown(f"<div class='tarjeta' style='margin-top:0.8rem;'><b>{usuario['Nombre']}</b><br>"
                    f"{insignia(usuario['Tipo'], '#2F8CEB')}</div>", unsafe_allow_html=True)
        eleccion = st.radio("Menú", list(menu.keys()), label_visibility="collapsed")
        st.write("")
        if st.button("Cerrar sesión", width="stretch"):
            bitacora(f"{usuario['Nombre']} cerró sesión")
            del st.session_state.usuario
            st.session_state.pop("atendiendo", None)
            st.rerun()
        st.caption("VetSmart · UABC · FCA")

    # Avisos que dejó la consulta del veterinario
    if st.session_state.get("aviso_consulta") is not None:
        st.success("Consulta guardada. El inventario se actualizó solo.")
        for aviso in st.session_state.aviso_consulta:
            st.warning(aviso)
        del st.session_state.aviso_consulta

    menu[eleccion]()


DATOS = obtener_datos()


def main():
    # Enlace de WhatsApp: ?cita=CT0001 abre la confirmación sin iniciar sesión
    id_cita = st.query_params.get("cita")
    if id_cita:
        pagina_confirmar_cita(id_cita)
        return

    if "usuario" not in st.session_state:
        pantalla_acceso()
    elif st.session_state.usuario["Tipo"] == "Cliente":
        portal_cliente()
    else:
        panel_personal()


main()
