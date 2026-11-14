import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

# Intentar importar winsound para alertas sonoras en Windows (fallback seguro en Mac/Linux)
try:
    import winsound
    TIENE_WINSOUND = True
except ImportError:
    TIENE_WINSOUND = False

# --- CONFIGURACIÓN DE COLORES Y FUENTES (ACCESIBILIDAD Y CONTRASTE) ---
COLOR_FONDO = "#F4F6F9"
COLOR_PRIMARIO = "#1B5E20"      # Verde oscuro institucional
COLOR_SECUNDARIO = "#2E7D32"    # Verde medio
COLOR_ACENTO = "#0277BD"        # Azul para acciones secundarias
COLOR_ALERTA = "#C62828"        # Rojo para alertas y stock bajo
COLOR_TARJETA = "#FFFFFF"
COLOR_TEXTO = "#1C2833"

FUENTE_TITULO = ("Segoe UI", 20, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 13, "bold")
FUENTE_NORMAL = ("Segoe UI", 11)
FUENTE_NEGRITA = ("Segoe UI", 11, "bold")
FUENTE_BOTON = ("Segoe UI", 12, "bold")

ARCHIVO_MEDICAMENTOS = "medicamentos.json"
ARCHIVO_HISTORIAL = "historial.json"


class DailyPillApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Daily Pill - Gestión y Recordatorio de Tratamientos")
        self.root.geometry("950x680")
        self.root.configure(bg=COLOR_FONDO)

        # Cargar datos locales (Modo Offline)
        self.medicamentos = self.cargar_datos(ARCHIVO_MEDICAMENTOS)
        self.historial = self.cargar_datos(ARCHIVO_HISTORIAL)
        self.alarmas_disparadas_hoy = set()

        self.construir_interfaz()
        self.actualizar_tabla_medicamentos()
        self.actualizar_tabla_historial()

        # Iniciar el reloj y verificador de alarmas en segundo plano
        self.verificar_reloj_y_alarmas()

    # --- MANEJO DE PERSISTENCIA LOCAL (JSON) ---
    def cargar_datos(self, ruta):
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def guardar_datos(self, ruta, datos):
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=4, ensure_ascii=False)

    # --- CONSTRUCCIÓN DE LA INTERFAZ GRÁFICA ---
    def construir_interfaz(self):
        # Encabezado superior
        header = tk.Frame(self.root, bg=COLOR_PRIMARIO, height=75)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="💊 DAILY PILL",
            font=FUENTE_TITULO,
            bg=COLOR_PRIMARIO,
            fg="white"
        ).pack(side="left", padx=25)

        self.lbl_reloj = tk.Label(
            header,
            text="00:00:00",
            font=("Segoe UI", 16, "bold"),
            bg=COLOR_PRIMARIO,
            fg="#E8F5E9"
        )
        self.lbl_reloj.pack(side="right", padx=25)

        # Contenedor principal de pestañas
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure("TNotebook.Tab", font=FUENTE_NEGRITA, padding=[15, 8])
        estilo.configure("Treeview", font=FUENTE_NORMAL, rowheight=32)
        estilo.configure("Treeview.Heading", font=FUENTE_NEGRITA, background="#E0E0E0")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=20, pady=15)

        # Pestaña 1: Tomas del Día y Confirmación
        self.tab_tomas = tk.Frame(notebook, bg=COLOR_FONDO)
        notebook.add(self.tab_tomas, text="📋 Tomas del Día")
        self.construir_tab_tomas()

        # Pestaña 2: Registrar Medicamento y Cuidador
        self.tab_registro = tk.Frame(notebook, bg=COLOR_FONDO)
        notebook.add(self.tab_registro, text="➕ Registrar Medicamento")
        self.construir_tab_registro()

        # Pestaña 3: Historial / Línea de Tiempo
        self.tab_historial = tk.Frame(notebook, bg=COLOR_FONDO)
        notebook.add(self.tab_historial, text="🕒 Historial de Adherencia")
        self.construir_tab_historial()

    def construir_tab_tomas(self):
        # Panel superior informativo
        info_frame = tk.Frame(self.tab_tomas, bg=COLOR_TARJETA, bd=1, relief="solid")
        info_frame.pack(fill="x", pady=(10, 15), ipady=10)

        tk.Label(
            info_frame,
            text="Tratamientos Activos del Paciente",
            font=FUENTE_SUBTITULO,
            bg=COLOR_TARJETA,
            fg=COLOR_PRIMARIO
        ).pack(side="left", padx=15)

        self.lbl_proxima = tk.Label(
            info_frame,
            text="Próxima toma: Sin programar",
            font=FUENTE_NEGRITA,
            bg=COLOR_TARJETA,
            fg=COLOR_ACENTO
        )
        self.lbl_proxima.pack(side="right", padx=15)

        # Tabla de medicamentos
        columnas = ("nombre", "dosis", "hora", "dias", "inventario", "cuidador")
        self.tree_meds = ttk.Treeview(self.tab_tomas, columns=columnas, show="headings", height=10)

        encabezados = {
            "nombre": "Medicamento",
            "dosis": "Dosis",
            "hora": "Hora (HH:MM)",
            "dias": "Frecuencia / Días",
            "inventario": "Pastillas Restantes",
            "cuidador": "Contacto Familiar"
        }

        for col, texto in encabezados.items():
            self.tree_meds.heading(col, text=texto)
            self.tree_meds.column(col, anchor="center", width=135)

        self.tree_meds.pack(fill="both", expand=True, pady=5)

        # Panel de botones grandes de acción (Accesibilidad)
        btn_frame = tk.Frame(self.tab_tomas, bg=COLOR_FONDO)
        btn_frame.pack(fill="x", pady=15)

        btn_confirmar = tk.Button(
            btn_frame,
            text="✅ CONFIRMAR TOMA DE MEDICAMENTO",
            font=FUENTE_BOTON,
            bg=COLOR_SECUNDARIO,
            fg="white",
            activebackground=COLOR_PRIMARIO,
            activeforeground="white",
            cursor="hand2",
            height=2,
            command=self.confirmar_toma_seleccionada
        )
        btn_confirmar.pack(side="left", fill="x", expand=True, padx=(0, 10))

        btn_eliminar = tk.Button(
            btn_frame,
            text="🗑️ Eliminar",
            font=FUENTE_BOTON,
            bg=COLOR_ALERTA,
            fg="white",
            cursor="hand2",
            height=2,
            width=15,
            command=self.eliminar_medicamento
        )
        btn_eliminar.pack(side="right")

    def construir_tab_registro(self):
        form_card = tk.Frame(self.tab_registro, bg=COLOR_TARJETA, bd=1, relief="solid", padx=30, pady=25)
        form_card.pack(fill="both", expand=True, pady=10)

        tk.Label(
            form_card,
            text="Agregar Nuevo Tratamiento Farmacológico",
            font=FUENTE_SUBTITULO,
            bg=COLOR_TARJETA,
            fg=COLOR_PRIMARIO
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 20))

        campos = [
            ("Nombre del Medicamento (ej. Losartán):", "entry_nombre"),
            ("Dosis Asignada (ej. 50 mg / 1 tableta):", "entry_dosis"),
            ("Hora de Toma (Formato 24h HH:MM, ej. 08:30):", "entry_hora"),
            ("Días de Toma (ej. Todos los días / Lun-Mie-Vie):", "entry_dias"),
            ("Inventario Inicial (Cantidad de pastillas):", "entry_stock"),
            ("Nombre y Teléfono del Cuidador / Familiar:", "entry_cuidador")
        ]

        self.entradas = {}
        for idx, (etiqueta, clave) in enumerate(campos, start=1):
            tk.Label(
                form_card,
                text=etiqueta,
                font=FUENTE_NEGRITA,
                bg=COLOR_TARJETA,
                fg=COLOR_TEXTO
            ).grid(row=idx, column=0, sticky="w", pady=8)

            entry = tk.Entry(form_card, font=FUENTE_NORMAL, width=38, bd=2, relief="groove")
            entry.grid(row=idx, column=1, sticky="w", padx=(20, 0), pady=8)
            self.entradas[clave] = entry

        btn_guardar = tk.Button(
            form_card,
            text="💾 GUARDAR TRATAMIENTO",
            font=FUENTE_BOTON,
            bg=COLOR_PRIMARIO,
            fg="white",
            cursor="hand2",
            height=2,
            command=self.registrar_medicamento
        )
        btn_guardar.grid(row=len(campos) + 1, column=0, columnspan=2, sticky="ew", pady=(25, 0))

    def construir_tab_historial(self):
        tk.Label(
            self.tab_historial,
            text="Línea de Tiempo de Dosis Administradas",
            font=FUENTE_SUBTITULO,
            bg=COLOR_FONDO,
            fg=COLOR_PRIMARIO
        ).pack(anchor="w", pady=(10, 10))

        columnas = ("fecha_hora", "medicamento", "dosis", "estado", "notificacion")
        self.tree_hist = ttk.Treeview(self.tab_historial, columns=columnas, show="headings", height=14)

        encabezados = {
            "fecha_hora": "Fecha y Hora de Confirmación",
            "medicamento": "Medicamento",
            "dosis": "Dosis",
            "estado": "Estado",
            "notificacion": "Aviso a Cuidador"
        }

        for col, texto in encabezados.items():
            self.tree_hist.heading(col, text=texto)
            self.tree_hist.column(col, anchor="center", width=165)

        self.tree_hist.pack(fill="both", expand=True)

    # --- LÓGICA DE NEGOCIO Y FUNCIONALIDADES ---
    def registrar_medicamento(self):
        nombre = self.entradas["entry_nombre"].get().strip()
        dosis = self.entradas["entry_dosis"].get().strip()
        hora = self.entradas["entry_hora"].get().strip()
        dias = self.entradas["entry_dias"].get().strip()
        stock_str = self.entradas["entry_stock"].get().strip()
        cuidador = self.entradas["entry_cuidador"].get().strip()

        if not all([nombre, dosis, hora, dias, stock_str, cuidador]):
            messagebox.showwarning("Campos Incompletos", "Por favor, completa todos los datos del tratamiento.")
            return

        # Validar formato de hora HH:MM
        try:
            datetime.strptime(hora, "%H:%M")
        except ValueError:
            messagebox.showerror("Formato Inválido", "La hora debe tener el formato HH:MM (ejemplo: 08:00 o 14:30).")
            return

        # Validar inventario numérico
        if not stock_str.isdigit():
            messagebox.showerror("Inventario Inválido", "La cantidad de pastillas debe ser un número entero.")
            return

        nuevo_med = {
            "id": int(datetime.now().timestamp() * 1000),
            "nombre": nombre,
            "dosis": dosis,
            "hora": hora,
            "dias": dias,
            "inventario": int(stock_str),
            "cuidador": cuidador
        }

        self.medicamentos.append(nuevo_med)
        self.guardar_datos(ARCHIVO_MEDICAMENTOS, self.medicamentos)
        self.actualizar_tabla_medicamentos()

        for entry in self.entradas.values():
            entry.delete(0, tk.END)

        messagebox.showinfo("Registro Exitoso", f"El medicamento '{nombre}' ha sido programado correctamente.")

    def actualizar_tabla_medicamentos(self):
        for item in self.tree_meds.get_children():
            self.tree_meds.delete(item)

        # Ordenar por hora más cercana
        self.medicamentos.sort(key=lambda m: m["hora"])

        for med in self.medicamentos:
            stock_texto = f"{med['inventario']} uds."
            if med["inventario"] <= 3:
                stock_texto += " ⚠️ (Reponer)"

            self.tree_meds.insert(
                "",
                "end",
                iid=str(med["id"]),
                values=(med["nombre"], med["dosis"], med["hora"], med["dias"], stock_texto, med["cuidador"])
            )

        self.calcular_proxima_toma()

    def calcular_proxima_toma(self):
        if not self.medicamentos:
            self.lbl_proxima.config(text="Próxima toma: Sin programar")
            return

        ahora_str = datetime.now().strftime("%H:%M")
        futuras = [m for m in self.medicamentos if m["hora"] >= ahora_str]

        proxima = futuras[0] if futuras else self.medicamentos[0]
        self.lbl_proxima.config(text=f"Próxima toma: {proxima['nombre']} a las {proxima['hora']}")

    def confirmar_toma_seleccionada(self):
        seleccion = self.tree_meds.selection()
        if not seleccion:
            messagebox.showwarning("Selección Requerida", "Selecciona un medicamento de la lista para confirmar su toma.")
            return

        med_id = int(seleccion[0])
        self.procesar_confirmacion(med_id)

    def procesar_confirmacion(self, med_id):
        for med in self.medicamentos:
            if med["id"] == med_id:
                if med["inventario"] > 0:
                    med["inventario"] -= 1

                marca_tiempo = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                registro = {
                    "fecha_hora": marca_tiempo,
                    "medicamento": med["nombre"],
                    "dosis": med["dosis"],
                    "estado": "✅ Administrada",
                    "notificacion": f"Enviado a {med['cuidador']}"
                }

                self.historial.insert(0, registro)
                self.guardar_datos(ARCHIVO_MEDICAMENTOS, self.medicamentos)
                self.guardar_datos(ARCHIVO_HISTORIAL, self.historial)

                self.actualizar_tabla_medicamentos()
                self.actualizar_tabla_historial()

                aviso = f"Toma de {med['nombre']} ({med['dosis']}) confirmada.\nNotificación en espejo generada para: {med['cuidador']}."
                if med["inventario"] <= 3:
                    aviso += f"\n\n⚠️ ALERTA DE INVENTARIO: Quedan solo {med['inventario']} pastillas."

                messagebox.showinfo("Toma Confirmada", aviso)
                break

    def eliminar_medicamento(self):
        seleccion = self.tree_meds.selection()
        if not seleccion:
            messagebox.showwarning("Selección Requerida", "Selecciona el medicamento que deseas eliminar.")
            return

        med_id = int(seleccion[0])
        self.medicamentos = [m for m in self.medicamentos if m["id"] != med_id]
        self.guardar_datos(ARCHIVO_MEDICAMENTOS, self.medicamentos)
        self.actualizar_tabla_medicamentos()

    def actualizar_tabla_historial(self):
        for item in self.tree_hist.get_children():
            self.tree_hist.delete(item)

        for reg in self.historial:
            self.tree_hist.insert(
                "",
                "end",
                values=(reg["fecha_hora"], reg["medicamento"], reg["dosis"], reg["estado"], reg["notificacion"])
            )

    # --- SISTEMA DE ALARMAS EN TIEMPO REAL ---
    def verificar_reloj_y_alarmas(self):
        ahora = datetime.now()
        self.lbl_reloj.config(text=ahora.strftime("%H:%M:%S"))

        hora_actual_hm = ahora.strftime("%H:%M")
        fecha_actual = ahora.strftime("%Y-%m-%d")

        for med in self.medicamentos:
            clave_alarma = f"{fecha_actual}_{med['id']}_{hora_actual_hm}"
            if med["hora"] == hora_actual_hm and clave_alarma not in self.alarmas_disparadas_hoy:
                self.alarmas_disparadas_hoy.add(clave_alarma)
                self.disparar_ventana_alarma(med)

        # Revisar cada 1000 ms (1 segundo)
        self.root.after(1000, self.verificar_reloj_y_alarmas)

    def disparar_ventana_alarma(self, med):
        if TIENE_WINSOUND:
            try:
                winsound.Beep(1000, 700)
            except RuntimeError:
                pass

        ventana_alerta = tk.Toplevel(self.root)
        ventana_alerta.title("⏰ ¡HORA DE TU MEDICAMENTO!")
        ventana_alerta.geometry("480x300")
        ventana_alerta.configure(bg="#FFF3E0")
        ventana_alerta.attributes("-topmost", True)

        tk.Label(
            ventana_alerta,
            text="⏰ RECORDATORIO DE TOMA",
            font=("Segoe UI", 16, "bold"),
            bg="#E65100",
            fg="white",
            pady=10
        ).pack(fill="x")

        tk.Label(
            ventana_alerta,
            text=f"Medicamento: {med['nombre']}\nDosis: {med['dosis']}\nHora programada: {med['hora']}",
            font=("Segoe UI", 13, "bold"),
            bg="#FFF3E0",
            fg=COLOR_TEXTO,
            pady=20
        ).pack()

        tk.Label(
            ventana_alerta,
            text=f"📲 Alerta espejo preparada para: {med['cuidador']}",
            font=("Segoe UI", 10, "italic"),
            bg="#FFF3E0",
            fg="#5D4037"
        ).pack(pady=(0, 15))

        tk.Button(
            ventana_alerta,
            text="✅ YA ME LA TOMÉ (CONFIRMAR)",
            font=FUENTE_BOTON,
            bg=COLOR_SECUNDARIO,
            fg="white",
            cursor="hand2",
            height=2,
            command=lambda: [self.procesar_confirmacion(med["id"]), ventana_alerta.destroy()]
        ).pack(fill="x", padx=30)


if __name__ == "__main__":
    ventana_principal = tk.Tk()
    app = DailyPillApp(ventana_principal)
    ventana_principal.mainloop()

    