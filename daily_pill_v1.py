from datetime import datetime


medicamentos = []

def mostrar_menu():
    print("\n" + "="*45)
    print("💊 DAILY PILL")
    print("="*45)
    print("1. Registrar nuevo medicamento")
    print("2. Ver tratamientos y calcular próxima toma")
    print("3. Confirmar toma de medicamento")
    print("4. Salir")
    print("="*45)

def registrar_medicamento():
    print("\n--- REGISTRAR MEDICAMENTO ---")
    nombre = input("Nombre del medicamento (ej. Losartán): ").strip()
    dosis = input("Dosis asignada (ej. 50 mg / 1 tableta): ").strip()
    
    while True:
        hora = input("Hora de toma (Formato 24h HH:MM, ej. 08:30): ").strip()
        try:
            datetime.strptime(hora, "%H:%M")
            break
        except ValueError:
            print("❌ Formato inválido. Usa HH:MM (ejemplo: 14:30).")

    dias = input("Frecuencia / Días (ej. Todos los días): ").strip()

    while True:
        stock_str = input("Cantidad de pastillas iniciales: ").strip()
        if stock_str.isdigit():
            inventario = int(stock_str)
            break
        print("❌ Por favor, ingresa un número entero válido.")

    nuevo_med = {
        "nombre": nombre,
        "dosis": dosis,
        "hora": hora,
        "dias": dias,
        "inventario": inventario
    }

    medicamentos.append(nuevo_med)
    print(f"\n✅ '{nombre}' registrado correctamente para las {hora}.")

def calcular_proxima_toma():
    if not medicamentos:
        return "Sin medicamentos programados."

    # Ordenar medicamentos por hora
    medicamentos.sort(key=lambda m: m["hora"])
    hora_actual = datetime.now().strftime("%H:%M")

    # Buscar el primer medicamento cuya hora sea mayor o igual a la actual
    futuras = [m for m in medicamentos if m["hora"] >= hora_actual]
    proxima = futuras[0] if futuras else medicamentos[0]

    return f"⏰ Próxima toma: {proxima['nombre']} ({proxima['dosis']}) a las {proxima['hora']}"

def ver_tratamientos():
    print("\n--- TRATAMIENTOS ACTIVOS ---")
    if not medicamentos:
        print("No hay medicamentos registrados todavía.")
        return

    print(calcular_proxima_toma())
    print("-" * 45)
    
    for idx, med in enumerate(medicamentos, start=1):
        alerta_stock = " ⚠️ (Stock bajo)" if med["inventario"] <= 3 else ""
        print(f"{idx}. {med['nombre']} | Dosis: {med['dosis']} | Hora: {med['hora']} | Restantes: {med['inventario']}{alerta_stock}")

def confirmar_toma():
    print("\n--- CONFIRMAR TOMA ---")
    if not medicamentos:
        print("No hay medicamentos para confirmar.")
        return

    ver_tratamientos()
    opcion = input("\nIngresa el número del medicamento que te tomaste (o '0' para cancelar): ").strip()

    if opcion == "0":
        return

    if opcion.isdigit() and 1 <= int(opcion) <= len(medicamentos):
        med = medicamentos[int(opcion) - 1]
        
        if med["inventario"] > 0:
            med["inventario"] -= 1
            hora_confirmacion = datetime.now().strftime("%H:%M:%S")
            print(f"\n✅ Toma de '{med['nombre']}' confirmada a las {hora_confirmacion}.")
            print(f"📦 Pastillas restantes: {med['inventario']}")
        else:
            print(f"\n⚠️ No quedan pastillas en el inventario de '{med['nombre']}'. ¡Debes reponer!")
    else:
        print("❌ Selección inválida.")

def iniciar_programa():
    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción (1-4): ").strip()

        if opcion == "1":
            registrar_medicamento()
        elif opcion == "2":
            ver_tratamientos()
        elif opcion == "3":
            confirmar_toma()
        elif opcion == "4":
            print("\n👋 Cerrando Daily Pill. ¡Cuida tu salud!")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    iniciar_programa()
