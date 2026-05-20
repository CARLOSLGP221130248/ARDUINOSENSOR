import serial
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import sys

# Configuración constante
FIREBASE_URL = 'https://monitoreo-de-temperatura-f5496-default-rtdb.firebaseio.com/'
PORT = 'COM3'
BAUD_RATE = 9600

def conectar_firebase():
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_URL})
        return db.reference('sensor_data')
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar Firebase: {e}")
        sys.exit(1)

def conectar_serial(puerto, baudios):
    while True:
        try:
            print(f"[INFO] Intentando conectar al puerto {puerto}...")
            ser = serial.Serial(puerto, baudios, timeout=1)
            time.sleep(2)
            print("[OK] Conexión serial establecida.")
            return ser
        except serial.SerialException:
            print("[RETRY] Puerto no disponible. Reintentando en 5 segundos...")
            time.sleep(5)

# Inicialización
ref = conectar_firebase()
ser = conectar_serial(PORT, BAUD_RATE)

while True:
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            if "HUMEDAD" in line and "TEMPERATURA" in line:
                now = datetime.now()
                
                # Parseo robusto
                parts = line.split(",")
                humedad_val = float(parts[0].split("=")[1].strip())
                temperatura_val = float(parts[1].split("=")[1].strip())
                
                data = {
                    "HUMEDAD": f"{humedad_val} %",
                    "TEMPERATURA": f"{temperatura_val} °C",
                    "DIA": now.strftime("%Y-%m-%d"),
                    "HORA": now.strftime("%H:%M:%S"),
                    "timestamp": time.time()
                }
                
                ref.push(data)
                print(f"[DATA] Enviado: T={temperatura_val}°C | H={humedad_val}%")
                
    except (serial.SerialException, SerialDisconnectException):
        print("\n[WARNING] Conexión perdida con Arduino. Reconectando...")
        ser.close()
        ser = conectar_serial(PORT, BAUD_RATE)
    except KeyboardInterrupt:
        print("\n[INFO] Script detenido por el usuario.")
        ser.close()
        break
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        time.sleep(2)