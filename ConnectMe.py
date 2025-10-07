import csv
import os

ARCHIVO = "contactos.csv"  

def cargar_contactos():
    contactos = []
    if not os.path.isfile(ARCHIVO):
        return contactos
    with open(ARCHIVO, newline='', encoding='') as f: 
        reader = csv.DictReader(f)
        for row in reader:
            contactos.append(row)
    return contactos


def guardar_contactos(contactos):
    with open(ARCHIVO, "w", newline='', encoding='utf-8') as f:
        campos = ["Nombre", "Telefono", "Email", "Cargo"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for c in contactos:
            writer.writerow(c)

def mostrar_contacto(c):
    return f"{c['Nombre']} | {c['Telefono']} | {c['Email']} | {c['Cargo']}"

def registrar_contacto(contactos):
    print("\nRegistrar nuevo contacto")
    nombre = input("Nombre: ").strip()
    telefono = input("Teléfono: ").strip()
    email = input("Email: ").strip().lower()
    cargo = input("Cargo: ").strip()
    if not nombre or not email:
        print("Nombre y Email son obligatorios.")
        return
        
    for c in contactos:
        if c["Email"].lower() == email:
            print("Ya existe un contacto con ese email.")
            return
    contactos.append({"Nombre": nombre, "Telefono": telefono, "Email": email, "Cargo": cargo})
    guardar_contactos(contactos)
    print("Contacto registrado.")

def buscar_contacto(contactos):
    q = input("\nBuscar por nombre o email: ").strip().lower()
    if not q:
        print("Consulta vacía.")
        return
    resultados = [c for c in contactos if q in c["Nombre"].lower() or q in c["Email"].lower()]
    if not resultados:
        print("No se encontraron contactos.")
        return
    print(f"\nSe encontraron {len(resultados)} contacto(s):")
    for i, c in enumerate(resultados, 1):
        print(f"{i}. {mostrar_contacto(c)}")

def listar_contactos(contactos):
    if not contactos:
        print("\nNo hay contactos registrados.")
        return
    print(f"\nLista de {len(contactos)} contacto(s):")
    for i, c in enumerate(contactos, 1):
        print(f"{i}. {mostrar_contacto(c)}")

def eliminar_contacto(contactos):
    listar_contactos(contactos)
    if not contactos:
        return
    clave = input("\nEliminar por número o por email (ingrese 'cancel' para salir): ").strip()
    if clave.lower() == "cancel":
        return
    # por número
    if clave.isdigit():
        idx = int(clave) - 1
        if 0 <= idx < len(contactos):
            eliminado = contactos.pop(idx)
            guardar_contactos(contactos)
            print("Contacto eliminado:", mostrar_contacto(eliminado))
            return
        else:
            print("Número inválido.")
            return
    # por email
    email = clave.lower()
    for i, c in enumerate(contactos):
        if c["Email"].lower() == email:
            eliminado = contactos.pop(i)
            guardar_contactos(contactos)
            print("Contacto eliminado:", mostrar_contacto(eliminado))
            return
    print("No se encontró un contacto con ese email.")

# menú principal
def main():
    contactos = cargar_contactos() 
    while True:
        print("\n--- Menú Contactos ---")
        print("1. Registrar contacto")
        print("2. Buscar contacto")
        print("3. Listar todos")
        print("4. Eliminar contacto")
        print("5. Salir")
        opcion = input("Seleccione opción (1-5): ").strip()
        if opcion == "1":
            registrar_contacto(contactos)
        elif opcion == "2":
            buscar_contacto(contactos)
        elif opcion == "3":
            listar_contactos(contactos)
        elif opcion == "4":
            eliminar_contacto(contactos)
        elif opcion == "5":
            print("Saliendo.")
            break
        else:
            print("Opción inválida. Intente de nuevo.")

if __name__ == "__main__":
    main()

