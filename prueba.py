#ACTIVIDAD 7 - Cine

import tkinter as tk
from tkinter import messagebox, StringVar, OptionMenu, Frame, IntVar, Radiobutton, Scale, Toplevel, PanedWindow, Label, Button, Canvas, Scrollbar
from tkcalendar import Calendar
from PIL import Image, ImageTk
import random
from pymongo import MongoClient
from datetime import datetime

# Configuración de MongoDB
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cine_db']
    reservas_collection = db['reservas']
    peliculas_collection = db['peliculas']
    salas_collection = db['salas']
    print("Conexión exitosa a MongoDB")
except Exception as e:
    print(f"Error al conectar con MongoDB: {e}")

# Funciones para inicializar la base de datos
def inicializar_base_datos():
    try:
        # Crear índices si no existen
        peliculas_collection.create_index("titulo")
        reservas_collection.create_index("fecha")
        reservas_collection.create_index("pelicula")
        salas_collection.create_index("numero")

        # Verificar si ya existen datos
        if peliculas_collection.count_documents({}) == 0:
            # Insertar películas predeterminadas
            peliculas_default = [
                {
                    "titulo": "Robot Salvaje",
                    "imagen": "robot_salvaje.jpg",
                    "horarios": ["13:00", "15:30", "18:00", "20:30"],
                    "version": ["Normal", "3D", "VIP"],
                    "precio": {"Normal": 100, "3D": 150, "VIP": 200}
                },
                # ... otras películas ...
            ]
            peliculas_collection.insert_many(peliculas_default)

        if salas_collection.count_documents({}) == 0:
            # Crear salas predeterminadas
            for numero_sala in range(1, 4):
                asientos = []
                for fila in range(6):
                    for col in range(8):
                        asientos.append({
                            "id": f"{chr(ord('A') + fila)}{col + 1}",
                            "estado": "Disponible"
                        })
                
                sala = {
                    "numero": numero_sala,
                    "capacidad": 48,
                    "tipo": "Normal",
                    "asientos": asientos
                }
                salas_collection.insert_one(sala)

        return True
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        return False

# Funciones para MongoDB
def guardar_reserva(pelicula, fecha, version, cantidad_entradas, asientos_seleccionados):
    try:
        # Obtener el precio de la película
        pelicula_info = peliculas_collection.find_one({"titulo": pelicula})
        precio_unitario = pelicula_info["precio"][version]
        total = precio_unitario * cantidad_entradas

        reserva = {
            'pelicula': pelicula,
            'fecha': fecha,
            'version': version,
            'cantidad_entradas': cantidad_entradas,
            'asientos': asientos_seleccionados,
            'fecha_reserva': datetime.now(),
            'total': total,
            'estado': 'Confirmada'
        }
        reservas_collection.insert_one(reserva)
        return True
    except Exception as e:
        print(f"Error al guardar la reserva: {e}")
        return False

def obtener_reservas():
    try:
        return list(reservas_collection.find())
    except Exception as e:
        print(f"Error al obtener reservas: {e}")
        return []

def guardar_pelicula(titulo, imagen, horarios, versiones=None, precios=None):
    if versiones is None:
        versiones = ["Normal", "3D", "VIP"]
    if precios is None:
        precios = {"Normal": 100, "3D": 150, "VIP": 200}

    pelicula = {
        'titulo': titulo,
        'imagen': imagen,
        'horarios': horarios,
        'version': versiones,
        'precio': precios
    }
    try:
        peliculas_collection.insert_one(pelicula)
        return True
    except Exception as e:
        print(f"Error al guardar la película: {e}")
        return False

def actualizar_estado_asiento(sala_numero, asiento_id, nuevo_estado):
    try:
        salas_collection.update_one(
            {"numero": sala_numero, "asientos.id": asiento_id},
            {"$set": {"asientos.$.estado": nuevo_estado}}
        )
        return True
    except Exception as e:
        print(f"Error al actualizar estado del asiento: {e}")
        return False

def obtener_asientos_disponibles(sala_numero):
    try:
        sala = salas_collection.find_one({"numero": sala_numero})
        return [asiento for asiento in sala["asientos"] if asiento["estado"] == "Disponible"]
    except Exception as e:
        print(f"Error al obtener asientos disponibles: {e}")
        return []

# Inicializar la base de datos al inicio
inicializar_base_datos()

def butacaCine():
    return [[(chr(ord('A') + i) + str(j), "Disponible") for j in range(1, 9)] for i in range(6)]

def ocupar_asientos(butacas):
    ocupados = random.sample([(i, j) for i in range(6) for j in range(8)], 5)
    for i, j in ocupados:
        butacas[i][j] = (butacas[i][j][0], "Ocupado")
    return butacas

def mostrarButacas(butacas):
    for widget in frame_asientos.winfo_children():
        widget.destroy()

    for i in range(6):
        for j in range(8):
            estado = butacas[i][j][1]
            icono = "\U0001F4BA" if estado == "Disponible" else "\U0001F464"
            texto = f"{butacas[i][j][0]} {icono}"

            boton = Button(
                frame_asientos, text=texto, relief="flat", bg="#F0F0F0",
                font=("Arial", 12), width=8, height=2,
                command=lambda fila=i, col=j: seleccionar_asiento(fila, col, butacas)
            )
            boton.grid(row=i, column=j, padx=5, pady=5)

def seleccionar_asiento(fila, col, butacas):
    if butacas[fila][col][1] == "Disponible":
        butacas[fila][col] = (butacas[fila][col][0], "Ocupado")
        mostrarButacas(butacas)

def actualizar_asientos(*args):
    butacas = butacaCine()
    butacas = ocupar_asientos(butacas)
    mostrarButacas(butacas)

def mostrar_resumen():
    # Obtener asientos seleccionados
    asientos_seleccionados = []
    for i in range(6):
        for j in range(8):
            if butacas[i][j][1] == "Ocupado":
                asientos_seleccionados.append(butacas[i][j][0])

    # Guardar en MongoDB
    if guardar_reserva(
        var_pelicula.get(),
        calendario.get_date(),
        opcion_version.get(),
        cantidad_entradas.get(),
        asientos_seleccionados
    ):
        messagebox.showinfo("Éxito", "Reserva guardada correctamente en la base de datos")
    else:
        messagebox.showerror("Error", "No se pudo guardar la reserva en la base de datos")

    resumen = (
        f"Película: {var_pelicula.get()}\n"
        f"Fecha: {calendario.get_date()}\n"
        f"Versión: {opcion_version.get()}\n"
        f"Cantidad de entradas: {cantidad_entradas.get()}\n"
        f"Asientos seleccionados: {', '.join(asientos_seleccionados)}"
    )
    resumen_ventana = Toplevel()
    resumen_ventana.title("Resumen de Reserva")
    resumen_ventana.iconbitmap("cine.ico")
    Label(resumen_ventana, text=resumen, padx=10, pady=10, font=("Arial", 14)).pack()
    Button(resumen_ventana, text="Cerrar", command=resumen_ventana.destroy, bg="steel blue", fg="white").pack(pady=5)
    Button(resumen_ventana, text="Imprimir Ticket", command=imprimir_ticket, bg="steel blue", fg="white").pack(pady=5)

def imprimir_ticket():
    with open("ticket_reserva.txt", "w") as ticket:
        ticket.write(
            f"Película: {var_pelicula.get()}\n"
            f"Fecha: {calendario.get_date()}\n"
            f"Versión: {opcion_version.get()}\n"
            f"Cantidad de entradas: {cantidad_entradas.get()}\n"
        )
    messagebox.showinfo("Impresión", "El ticket se ha guardado correctamente.")


def mostrar_cartelera():
    cartelera_window = Toplevel(root)
    cartelera_window.title("Cartelera Cinépolis")
    cartelera_window.iconbitmap("cine.ico")
    cartelera_window.geometry("1000x800")
    cartelera_window.configure(bg="#ECECEC")
    
    # Frame con scroll para la cartelera
    cartelera_frame = Frame(cartelera_window, bg="#ECECEC")
    cartelera_canvas = Canvas(cartelera_frame, bg="#ECECEC")
    scrollbar = Scrollbar(cartelera_frame, orient="vertical", command=cartelera_canvas.yview)
    scrollable_cartelera = Frame(cartelera_canvas, bg="#ECECEC")

    scrollable_cartelera.bind(
        "<Configure>",
        lambda e: cartelera_canvas.configure(scrollregion=cartelera_canvas.bbox("all"))
    )

    cartelera_canvas.create_window((0, 0), window=scrollable_cartelera, anchor="nw")
    cartelera_canvas.configure(yscrollcommand=scrollbar.set)

    # Obtener películas desde MongoDB
    try:
        peliculas_info = list(peliculas_collection.find())
        if not peliculas_info:
            # Si no hay películas en la base de datos, insertar las predeterminadas
            peliculas_default = [
                {"titulo": "Robot Salvaje", "imagen": "robot_salvaje.jpg", "horarios": ["13:00", "15:30", "18:00", "20:30"]},
                {"titulo": "Transformers One", "imagen": "Transformers_One.jpg", "horarios": ["14:00", "16:30", "19:00", "21:30"]},
                {"titulo": "My Hero Academia", "imagen": "mha.jpeg", "horarios": ["12:30", "15:00", "17:30", "20:00"]},
                {"titulo": "La Sustancia", "imagen": "sustancia.jpg", "horarios": ["13:30", "16:00", "18:30", "21:00"]},
                {"titulo": "Smile 2", "imagen": "smile2.jpg", "horarios": ["14:30", "17:00", "19:30", "22:00"]},
                {"titulo": "Un viaje al corazón", "imagen": "uvac.jpg", "horarios": ["12:00", "14:30", "17:00", "19:30"]},
                {"titulo": "El conde de Montecristo", "imagen": "conde.jpg", "horarios": ["13:00", "15:30", "18:00", "20:30"]},
                {"titulo": "Joker 2", "imagen": "joker.jpg", "horarios": ["14:00", "16:30", "19:00", "21:30"]}
            ]
            for pelicula in peliculas_default:
                guardar_pelicula(pelicula["titulo"], pelicula["imagen"], pelicula["horarios"])
            peliculas_info = peliculas_default
    except Exception as e:
        print(f"Error al obtener películas de MongoDB: {e}")
        messagebox.showerror("Error", "No se pudieron cargar las películas desde la base de datos")
        return

    # Crear grid de películas (4 columnas)
    for i, pelicula in enumerate(peliculas_info):
        movie_frame = Frame(scrollable_cartelera, bg="white", bd=1, relief="solid")
        movie_frame.grid(row=i//4, column=i%4, padx=10, pady=10, sticky="nsew")

        try:
            img = Image.open(pelicula["imagen"])
            img = img.resize((200, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_label = Label(movie_frame, image=photo, bg="white")
            img_label.image = photo
            img_label.pack(pady=5)
        except Exception as e:
            Label(movie_frame, text="[Imagen no disponible]", 
                  bg="gray", width=25, height=10).pack(pady=5)

        Label(movie_frame, text=pelicula["titulo"], 
              font=("Arial", 12, "bold"), bg="white").pack(pady=5)

        horarios_frame = Frame(movie_frame, bg="white")
        horarios_frame.pack(pady=5)
        Label(horarios_frame, text="Horarios:", 
              font=("Arial", 10, "bold"), bg="white").pack()
        
        for horario in pelicula["horarios"]:
            Label(horarios_frame, text=horario, bg="white").pack(side="left", padx=5)

        Button(movie_frame, text="Seleccionar", 
               command=lambda p=pelicula["titulo"]: seleccionar_pelicula_cartelera(p, cartelera_window),
               bg="steel blue", fg="white").pack(pady=10)

    cartelera_frame.pack(fill="both", expand=True)
    cartelera_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

def seleccionar_pelicula_cartelera(pelicula, ventana_cartelera):
    var_pelicula.set(pelicula)
    ventana_cartelera.destroy()

# Ventana principal
root = tk.Tk()
root.title("Sistema de Reservas de Cine")
root.geometry("900x700")
root.config(bg="#ECECEC")
root.iconbitmap("cine.ico")

# Frame del encabezado con logo y botón de "VER CARTELERA"
header_frame = Frame(root, bg="#002B7A", height=100)
header_frame.pack(fill="x", side="top")
header_frame.pack_propagate(False)

try:
    logo_img = Image.open("cinepolisLogo.png")
    logo_img = logo_img.resize((200, 60), Image.Resampling.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = Label(header_frame, image=logo_photo, bg="#002B7A")
    logo_label.image = logo_photo
    logo_label.pack(side="left", padx=20, pady=20)
except Exception as e:
    #print(f"Error al cargar el logo: {e}")
    Label(header_frame, text="CINÉPOLIS", font=("Arial", 24, "bold"), fg="white", bg="#002B7A").pack(side="left", padx=20, pady=20)


Button(
    header_frame, text="VER CARTELERA", font=("Arial", 12, "bold"), 
    bg="#FFB41F", fg="black", relief="flat", 
    command=mostrar_cartelera  
).pack(side="right", padx=20, pady=30)


# Crear PanedWindow principal
main_paned = PanedWindow(root, orient="horizontal", sashrelief="raised", bg="#D6D6D6")
main_paned.pack(fill="both", expand=True)

# Panel izquierdo con Scrollbar
panel_izquierdo = Frame(main_paned, bg="#ECECEC")
canvas = Canvas(panel_izquierdo, bg="#ECECEC", highlightthickness=0)

scrollbar = Scrollbar(panel_izquierdo, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)
scrollable_frame = Frame(canvas, bg="#ECECEC")


scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
main_paned.add(panel_izquierdo, minsize=300)

# Opciones de películas
peliculas = [
    "Robot Salvaje", "Transformers One", "My Hero Academia (película)",
    "La Sustancia", "Smile 2", "Un viaje al corazón",
    "El conde de Montecristo", "Joker 2"
]
var_pelicula = StringVar(value=peliculas[0])
var_pelicula.trace("w", actualizar_asientos)

Label(scrollable_frame, text="Seleccione la película:", bg="#ECECEC", font=("Arial", 14)).pack(pady=10)
OptionMenu(scrollable_frame, var_pelicula, *peliculas).pack(pady=10)

Label(scrollable_frame, text="Seleccione la fecha:", bg="#ECECEC", font=("Arial", 14)).pack(pady=10)
calendario = Calendar(scrollable_frame, selectmode='day', date_pattern="dd-MM-yyyy")
calendario.pack(padx=10, pady=5)

Label(scrollable_frame, text="Opciones:", bg="#ECECEC", font=("Arial", 14)).pack(pady=10)
opcion_version = StringVar(value="Normal")
Radiobutton(scrollable_frame, text="Normal", variable=opcion_version, value="Normal", bg="#ECECEC").pack(anchor="w", padx=10)
Radiobutton(scrollable_frame, text="3D", variable=opcion_version, value="3D", bg="#ECECEC").pack(anchor="w", padx=10)
Radiobutton(scrollable_frame, text="VIP", variable=opcion_version, value="VIP", bg="#ECECEC").pack(anchor="w", padx=10)

Label(scrollable_frame, text="Cantidad de entradas:", bg="#ECECEC", font=("Arial", 14)).pack(pady=10)
cantidad_entradas = IntVar(value=1)
Scale(scrollable_frame, from_=1, to=15, orient="horizontal", variable=cantidad_entradas).pack(padx=10, pady=5)

Button(scrollable_frame, text="Reservar Función", command=mostrar_resumen, bg="steel blue", fg="white").pack(pady=10)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Panel derecho (asientos)
panel_derecho = Frame(main_paned, bg="#ECECEC")
main_paned.add(panel_derecho)

frame_asientos = Frame(panel_derecho, bg="#ECECEC")
frame_asientos.pack()

frame_simbologia = Frame(panel_derecho, bg="#ECECEC")
Label(frame_simbologia, text="\U0001F4BA Disponible", bg="#ECECEC", font=("Arial", 12)).pack(side="left", padx=10)
Label(frame_simbologia, text="\U0001F464 Ocupado", bg="#ECECEC", font=("Arial", 12)).pack(side="left", padx=10)
frame_simbologia.pack(pady=10)

actualizar_asientos()

def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

scrollable_frame.bind("<Configure>", on_frame_configure)


root.mainloop()
