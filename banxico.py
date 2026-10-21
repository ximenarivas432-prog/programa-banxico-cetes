"""
Programa de Banxico y CETES
Autor: Ximena Rivas Corredor
Fecha: 20/10/2026
Objetivo: Consultar Banxico, calcular CETES y enviar un reporte.
"""
import os
import random
import re
import smtplib
import requests
from dotenv import load_dotenv
from email.mime.text import MIMEText

load_dotenv()
TOKEN = os.getenv("BANXICO_TOKEN")
CORREO = os.getenv("CORREO")
CLAVE = os.getenv("CLAVE_APP")

# Series de ejemplo. La de CETES a 28 días es SF43783.
SERIES = {"SF43783": "CETES 28 días", "SF43718": "Serie de tasas Banxico"}
SERIE_CETES = "SF43783"

def consultar(serie):
    """Obtiene el último dato disponible de una serie."""
    if not TOKEN:
        print("Falta el token en el archivo .env")
        return None
    url = f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/oportuno"
    try:
        respuesta = requests.get(url, headers={"Bmx-Token": TOKEN}, timeout=15)
        respuesta.raise_for_status()
        info = respuesta.json()["bmx"]["series"][0]["datos"][0]
        tasa = float(info["dato"].replace(",", ""))
        print(f"Serie: {serie} | Fecha: {info['fecha']} | Dato: {tasa}")
        return tasa, info["fecha"]
    except requests.exceptions.RequestException as error:
        print("Error de conexión o respuesta:", error)
    except (KeyError, IndexError, ValueError, TypeError) as error:
        print("Error al leer datos de Banxico:", error)
    return None

def calcular_cetes(monto, tasa, dias=28):
    """Estima la compra de CETES completos con valor nominal de 10 pesos."""
    precio = 10 / (1 + (tasa / 100) * dias / 360)
    titulos = int(monto // precio)
    inversion = titulos * precio
    vencimiento = titulos * 10
    ganancia = vencimiento - inversion
    return precio, titulos, inversion, ganancia, vencimiento


def enviar_correo(destino, reporte):
    """Envia el reporte de CETES por Gmail en texto plano."""

    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", destino):
        print("El correo no es valido.")
        return

    if not CORREO or not CLAVE:
        print("Faltan los datos de Gmail en el archivo .env")
        return

    try:
        import ssl

        print("1. Conectando con Gmail...")

        contexto = ssl.create_default_context()

        with smtplib.SMTP_SSL(
            "smtp.gmail.com",
            465,
            timeout=20,
            context=contexto
        ) as servidor:

            print("2. Conexion establecida")

            servidor.login(CORREO, CLAVE)
            print("3. Inicio de sesion exitoso")

            mensaje = MIMEText(reporte, "plain", "utf-8")
            mensaje["Subject"] = "Reporte de inversion CETES"
            mensaje["From"] = CORREO
            mensaje["To"] = destino

            servidor.send_message(mensaje)

            print("4. Mensaje aceptado por Gmail")

        print("Revisa el correo del destinatario.")

    except smtplib.SMTPAuthenticationError:
        print("Error: Gmail rechazo las credenciales.")

    except (smtplib.SMTPException, OSError) as error:
        print("No se pudo enviar el correo:")
        print(type(error).__name__)
        print(error)

def opcion_cetes():
    """Consulta la tasa, pide el monto y prepara el informe."""
    dato = consultar(SERIE_CETES)
    if dato is None:
        return
    tasa, fecha = dato
    try:
        monto = float(input("¿Cuánto dinero quieres invertir? $").replace(",", ""))
        if monto <= 0:
            print("El monto debe ser mayor a cero.")
            return
    except ValueError:
        print("Escribe una cantidad numérica.")
        return
    precio, titulos, inversion, ganancia, total = calcular_cetes(monto, tasa)
    if titulos == 0:
        print("El monto no alcanza para comprar un CETE completo.")
        return
    reporte = (
        "\nREPORTE DE CETES A 28 DÍAS\n"
        f"Fecha del dato: {fecha}\n"
        f"Serie: {SERIE_CETES}\n"
        f"Tasa anual: {tasa:.4f}%\n"
        f"Dinero disponible: ${monto:,.2f}\n"
        f"Precio estimado por CETE: ${precio:.4f}\n"
        f"Títulos comprados: {titulos}\n"
        f"Inversión utilizada: ${inversion:,.2f}\n"
        f"Dinero sin invertir: ${monto-inversion:,.2f}\n"
        f"Ganancia estimada: ${ganancia:,.2f}\n"
        f"Valor al vencimiento: ${total:,.2f}\n"
        "Cálculo aproximado, sin impuestos ni comisiones.\n"
    )
    print(reporte)
    destino = input("Correo al que enviarás el reporte: ").strip()
    enviar_correo(destino, reporte)

def menu():
    """Muestra las tres opciones hasta que el usuario sale."""
    while True:
        print("\n--- MENÚ BANXICO ---")
        print("1. Consultar serie aleatoria")
        print("2. Consultar CETES y calcular")
        print("3. Salir")
        opcion = input("Elige 1, 2 o 3: ").strip()
        if opcion == "1":
            serie = random.choice(list(SERIES))
            print("Serie elegida:", SERIES[serie])
            consultar(serie)
        elif opcion == "2":
            opcion_cetes()
        elif opcion == "3":
            print("Adiós")
            break
        else:
            print("Opción incorrecta.")

if __name__ == "__main__":
    menu()
