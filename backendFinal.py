import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText
from flask_cors import CORS # Para permitir que tu frontend (en otro puerto) se conecte

app = Flask(__name__)
CORS(app) # Habilita CORS para todas las rutas, necesario para el frontend

# --- SIMULACIÓN DE BASE DE DATOS EN MEMORIA ---
# Estos datos se reinician cada vez que el servidor se detiene y se inicia.

# Datos de usuarios (simulados)
users_db = {} # {email: {username, password_hash}}

# Datos de commodities (simulados)
commodities_db = {
    "oro": {
        "id": 1,
        "name": "Oro",
        "symbol": "XAU",
        "description": "Metal precioso",
        "icon_url": "https://placehold.co/40x40/yellow/white?text=ORO",
        "current_price": 1950.75,
        "change": 1.2,
        "change_amount": 23.10,
        "high": 1965.40,
        "low": 1945.20,
        "history": {
            '1D': [1940, 1945, 1950, 1948, 1955, 1950.75],
            '1S': [1880, 1895, 1910, 1905, 1930, 1950.75],
            '1M': [1800, 1850, 1820, 1900, 1920, 1950.75],
            '3M': [1750, 1780, 1820, 1880, 1910, 1950.75],
            '1A': [1700, 1720, 1780, 1850, 1900, 1950.75],
            '5A': [1500, 1600, 1700, 1800, 1900, 1950.75]
        },
        "news": [
            {"title": "El oro alcanza máximos de 3 meses por tensiones geopolíticas", "source": "Reuters", "time": "Hace 3 horas", "snippet": "Los precios del oro subieron hoy un 1.2% debido a la mayor aversión al riesgo...", "url": "https://example.com/news/gold-geopolitics"},
            {"title": "Analistas proyectan un Q2 positivo para los metales preciosos", "source": "Bloomberg", "time": "Hace 5 horas", "snippet": "Según el último informe de Goldman Sachs, el oro podría alcanzar...", "url": "https://example.com/news/gold-q2"}
        ]
    },
    "petroleo": {
        "id": 2,
        "name": "Petróleo Brent",
        "symbol": "BZ",
        "description": "Crudo de referencia",
        "icon_url": "https://placehold.co/40x40/black/white?text=PET",
        "current_price": 78.45,
        "change": -0.8,
        "change_amount": -0.63,
        "high": 79.30,
        "low": 78.20,
        "history": {
            '1D': [78.80, 78.60, 78.40, 78.50, 78.30, 78.45],
            '1S': [75.00, 76.50, 77.00, 78.00, 79.00, 78.45],
            '1M': [70.00, 72.00, 74.00, 76.00, 78.00, 78.45],
            '3M': [65.00, 68.00, 72.00, 75.00, 77.00, 78.45],
            '1A': [60.00, 65.00, 70.00, 75.00, 78.00, 78.45],
            '5A': [50.00, 55.00, 60.00, 70.00, 75.00, 78.45]
        },
        "news": [
            {"title": "La OPEP+ considera recortes adicionales de producción", "source": "Reuters", "time": "Hace 1 hora", "snippet": "Los ministros de energía de la OPEP+ se reunirán para discutir la estabilidad del mercado...", "url": "https://example.com/news/oil-opec"},
            {"title": "Demanda de petróleo en China se recupera más rápido de lo esperado", "source": "Financial Times", "time": "Hace 4 horas", "snippet": "El consumo de combustible en China ha mostrado un repunte significativo...", "url": "https://example.com/news/oil-china"}
        ]
    },
    "cobre": {
        "id": 3,
        "name": "Cobre",
        "symbol": "HG",
        "description": "Metal industrial",
        "icon_url": "https://placehold.co/40x40/orange/white?text=COB",
        "current_price": 3.85,
        "change": 0.5,
        "change_amount": 0.019,
        "high": 3.88,
        "low": 3.83,
        "history": {
            '1D': [3.83, 3.84, 3.85, 3.84, 3.86, 3.85],
            '1S': [3.70, 3.75, 3.80, 3.82, 3.84, 3.85],
            '1M': [3.60, 3.65, 3.70, 3.75, 3.80, 3.85],
            '3M': [3.50, 3.55, 3.60, 3.70, 3.78, 3.85],
            '1A': [3.40, 3.45, 3.50, 3.60, 3.70, 3.85],
            '5A': [3.00, 3.20, 3.40, 3.60, 3.80, 3.85]
        },
        "news": [
            {"title": "La demanda de cobre se dispara por la electrificación global", "source": "Mining.com", "time": "Hace 6 horas", "snippet": "El metal rojo es crucial para la transición energética y la fabricación de vehículos eléctricos...", "url": "https://example.com/news/copper-ev"},
            {"title": "Nuevas minas de cobre en Chile prometen aumentar la oferta", "source": "El Mercurio", "time": "Ayer", "snippet": "Proyectos de expansión en el norte de Chile buscan satisfacer la creciente demanda...", "url": "https://example.com/news/copper-chile"}
        ]
    },
    "plata": {
        "id": 4,
        "name": "Plata",
        "symbol": "XAG",
        "description": "Metal precioso y industrial",
        "icon_url": "https://placehold.co/40x40/gray/white?text=PLA",
        "current_price": 23.10,
        "change": 0.7,
        "change_amount": 0.16,
        "high": 23.25,
        "low": 23.05,
        "history": {
            '1D': [23.00, 23.05, 23.10, 23.08, 23.15, 23.10],
            '1S': [22.50, 22.70, 22.80, 22.90, 23.00, 23.10],
            '1M': [22.00, 22.20, 22.40, 22.60, 22.80, 23.10],
            '3M': [21.50, 21.70, 22.00, 22.30, 22.60, 23.10],
            '1A': [20.00, 20.50, 21.00, 21.50, 22.00, 23.10],
            '5A': [18.00, 19.00, 20.00, 21.00, 22.00, 23.10]
        },
        "news": [
            {"title": "La plata sigue al oro en su rally alcista", "source": "Kitco News", "time": "Hace 2 horas", "snippet": "El metal blanco se beneficia de la incertidumbre económica y la demanda industrial...", "url": "https://example.com/news/silver-rally"},
            {"title": "Innovaciones en paneles solares aumentan la demanda de plata", "source": "Solar Power World", "time": "Hace 7 horas", "snippet": "La eficiencia de las celdas solares depende en gran medida de la plata...", "url": "https://example.com/news/silver-solar"}
        ]
    }
}

# Datos de noticias generales (simulados)
general_news_db = [
    {"title": "Los mercados de commodities enfrentan volatilidad por nuevas políticas comerciales", "source": "Reuters", "time": "Hace 2 horas", "snippet": "Los precios de las materias primas experimentaron fuertes fluctuaciones esta semana después del anuncio de nuevas...", "url": "https://example.com/news/market-volatility"},
    {"title": "Transición energética impulsa demanda de metales estratégicos", "source": "Bloomberg", "time": "Hace 5 horas", "snippet": "El cobre, níquel y litio están experimentando un aumento sin precedentes en su demanda mientras...", "url": "https://example.com/news/energy-transition"},
    {"title": "Cuellos de botella en la cadena de suministro afectan precios de commodities", "source": "Financial Times", "time": "Ayer", "snippet": "Los continuos problemas logísticos en los principales puertos del mundo están generando...", "url": "https://example.com/news/supply-chain"},
    {"title": "Precios de granos suben por preocupaciones climáticas", "source": "AgriNews", "time": "Hace 1 día", "snippet": "La sequía en regiones clave de producción agrícola está impulsando los precios del maíz y la soja...", "url": "https://example.com/news/grains-weather"},
    {"title": "Inversión en metales preciosos como refugio seguro", "source": "Goldman Sachs", "time": "Hace 2 días", "snippet": "Ante la incertidumbre económica global, los inversores están recurriendo al oro y la plata...", "url": "https://example.com/news/precious-metals-safe-haven"},
    {"title": "El futuro del gas natural en la transición energética", "source": "OilPrice.com", "time": "Hace 3 días", "snippet": "A medida que el mundo busca fuentes de energía más limpias, el gas natural juega un papel crucial...", "url": "https://example.com/news/natural-gas-future"}
]

# Datos de ubicaciones mineras (simulados)
mining_locations_db = [
    {"name": "Mina de Oro La Colosa", "position": [4.3389, -75.3872], "production": "high", "type": "Oro"},
    {"name": "Mina de Carbón Cerrejón", "position": [11.0884, -72.6696], "production": "high", "type": "Carbón"},
    {"name": "Mina de Esmeraldas Muzo", "position": [5.53, -74.12], "production": "medium", "type": "Esmeraldas"},
    {"name": "Mina de Níquel Cerro Matoso", "position": [8.38, -75.6], "production": "high", "type": "Níquel"},
    {"name": "Mina de Cobre El Roble", "position": [5.99, -75.78], "production": "medium", "type": "Cobre"},
    {"name": "Mina de Sal Zipaquirá", "position": [5.025, -74.005], "production": "low", "type": "Sal"}
]

# --- Configuración de Correo Electrónico (para simulación) ---
# Para un envío real, necesitarías configurar un servidor SMTP o usar un servicio como SendGrid.
# Estas son variables de entorno que deberías definir en un archivo .env si las usas realmente.
# SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.example.com')
# SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
# SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'your_email@example.com')
# SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your_email_password')
# SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'no-reply@commoditytrader.com')

# --- Rutas de la API ---

@app.route('/')
def home():
    return "Backend de Commodity Trader funcionando. ¡Conéctate desde tu frontend!"

# 1. API para obtener precios y datos de commodities
@app.route('/api/commodities', methods=['GET'])
def get_commodities():
    """
    Retorna una lista de todas las commodities disponibles con sus datos actuales.
    """
    commodities_list = []
    for key, data in commodities_db.items():
        # Crear una copia para no modificar el original y añadir solo datos relevantes
        commodity_info = {
            "key": key, # Añadir la clave para fácil referencia en el frontend
            "name": data["name"],
            "symbol": data["symbol"],
            "icon_url": data["icon_url"],
            "current_price": data["current_price"],
            "change": data["change"],
            "high": data["high"],
            "low": data["low"]
        }
        commodities_list.append(commodity_info)
    return jsonify(commodities_list)

@app.route('/api/commodity/<string:commodity_key>', methods=['GET'])
def get_commodity_details(commodity_key):
    """
    Retorna los detalles completos de una commodity específica, incluyendo historial y noticias.
    """
    commodity_data = commodities_db.get(commodity_key)
    if not commodity_data:
        return jsonify({"error": "Commodity no encontrada"}), 404
    
    # En un escenario real, el historial y las noticias se filtrarían por la commodity_id
    # Aquí, ya están pre-filtrados en la simulación.
    return jsonify(commodity_data)

# 2. API o simulador financiero
@app.route('/api/simulate_investment', methods=['POST'])
def simulate_investment():
    """
    Calcula la proyección de inversión basada en el monto, horizonte y escenario.
    """
    data = request.get_json()
    amount = data.get('amount')
    horizon = data.get('horizon')
    scenario = data.get('scenario')

    if not all([amount, horizon, scenario]):
        return jsonify({"error": "Faltan parámetros: amount, horizon, scenario"}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"error": "Monto de inversión inválido"}), 400

    projected_value = amount
    period_text = ""

    # Lógica de simulación simplificada (igual que en el frontend)
    if horizon == 'short':
        period_text = '1-3 meses'
        if scenario == 'optimistic': projected_value *= 1.05
        elif scenario == 'neutral': projected_value *= 1.01
        else: projected_value *= 0.98
    elif horizon == 'medium':
        period_text = '6-12 meses'
        if scenario == 'optimistic': projected_value *= 1.15
        elif scenario == 'neutral': projected_value *= 1.05
        else: projected_value *= 0.90
    elif horizon == 'long':
        period_text = '1-5 años'
        if scenario == 'optimistic': projected_value *= 1.30
        elif scenario == 'neutral': projected_value *= 1.10
        else: projected_value *= 0.80
    else:
        return jsonify({"error": "Horizonte temporal inválido"}), 400

    percentage_change = ((projected_value - amount) / amount) * 100

    return jsonify({
        "initial_investment": round(amount, 2),
        "projected_value": round(projected_value, 2),
        "percentage_change": round(percentage_change, 2),
        "period": period_text
    })

# 3. API para comparar commodities
@app.route('/api/compare_commodities', methods=['POST'])
def compare_commodities():
    """
    Retorna datos históricos de dos commodities para comparación.
    """
    data = request.get_json()
    commodity1_key = data.get('commodity1')
    commodity2_key = data.get('commodity2')
    period = data.get('period')

    if not all([commodity1_key, commodity2_key, period]):
        return jsonify({"error": "Faltan parámetros: commodity1, commodity2, period"}), 400

    comm1_data = commodities_db.get(commodity1_key)
    comm2_data = commodities_db.get(commodity2_key)

    if not comm1_data or not comm2_data:
        return jsonify({"error": "Una o ambas commodities no encontradas"}), 404
    
    if period not in comm1_data["history"] or period not in comm2_data["history"]:
        return jsonify({"error": "Período histórico no disponible para una o ambas commodities"}), 400

    # En un escenario real, las etiquetas (labels) del eje X se generarían dinámicamente
    # basándose en el período y las fechas reales de los datos.
    labels = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'] # Simplificado

    return jsonify({
        "labels": labels[:len(comm1_data["history"][period])], # Ajustar labels a la longitud de los datos
        "datasets": [
            {
                "label": comm1_data["name"],
                "data": comm1_data["history"][period]
            },
            {
                "label": comm2_data["name"],
                "data": comm2_data["history"][period]
            }
        ]
    })

# 4. API para enviar cotizaciones por correo
@app.route('/api/send_quote_email', methods=['POST'])
def send_quote_email():
    """
    Simula el envío de una cotización por correo electrónico.
    """
    data = request.get_json()
    recipient_email = data.get('email')
    commodity_name = data.get('commodity_name')
    quote_details = data.get('quote_details') # Detalles de la cotización a enviar

    if not all([recipient_email, commodity_name, quote_details]):
        return jsonify({"error": "Faltan parámetros: email, commodity_name, quote_details"}), 400

    # --- SIMULACIÓN DE ENVÍO DE CORREO ---
    print(f"Simulando envío de correo a: {recipient_email}")
    print(f"Asunto: Cotización de {commodity_name} de Commodity Trader")
    print(f"Contenido: {quote_details}")
    print("--- Fin de simulación de correo ---")

    # Para un envío real, descomentar y configurar esto:
    # try:
    #     msg = MIMEText(quote_details)
    #     msg['Subject'] = f"Cotización de {commodity_name} de Commodity Trader"
    #     msg['From'] = SENDER_EMAIL
    #     msg['To'] = recipient_email

    #     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    #         server.starttls() # Habilitar seguridad TLS
    #         server.login(SMTP_USERNAME, SMTP_PASSWORD)
    #         server.send_message(msg)
    #     return jsonify({"message": "Correo de cotización enviado exitosamente"}), 200
    # except Exception as e:
    #     print(f"Error al enviar correo: {e}")
    #     return jsonify({"error": "Error al enviar correo", "details": str(e)}), 500

    return jsonify({"message": "Simulación de envío de correo exitosa. (Funcionalidad real requiere configuración SMTP)"}), 200

# 5. API para obtener noticias relacionadas
@app.route('/api/news', methods=['GET'])
def get_news():
    """
    Retorna una lista de noticias destacadas, opcionalmente filtradas por commodity.
    """
    commodity_key = request.args.get('commodity') # Obtener parámetro de consulta

    if commodity_key:
        commodity_data = commodities_db.get(commodity_key)
        if commodity_data and "news" in commodity_data:
            return jsonify(commodity_data["news"])
        else:
            return jsonify({"error": "Noticias no encontradas para esta commodity"}), 404
    else:
        # Retornar noticias generales si no se especifica commodity
        return jsonify(general_news_db)

# 6. API para obtener datos del mapa minero
@app.route('/api/mining_locations', methods=['GET'])
def get_mining_locations():
    """
    Retorna la lista de ubicaciones de producción minera.
    """
    return jsonify(mining_locations_db)

# 7. API para registro de usuarios
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password') # En un sistema real, esto sería un hash

    if not all([username, email, password]):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    
    if email in users_db:
        return jsonify({"error": "El correo electrónico ya está registrado"}), 409
    
    if username in [u['username'] for u in users_db.values()]:
        return jsonify({"error": "El nombre de usuario ya está en uso"}), 409

    # Simulación de hash de contraseña (en un sistema real usarías bcrypt)
    password_hash = f"hashed_{password}" 
    
    users_db[email] = {
        "username": username,
        "password_hash": password_hash,
        "created_at": datetime.utcnow().isoformat()
    }
    print(f"Usuario registrado: {username} ({email})")
    return jsonify({"message": "Registro exitoso", "user": {"username": username, "email": email}}), 201

# 8. API para inicio de sesión
@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    
    user_data = users_db.get(email)
    if not user_data:
        return jsonify({"error": "Credenciales inválidas"}), 401
    
    # Simulación de verificación de contraseña
    if user_data["password_hash"] == f"hashed_{password}":
        # En un sistema real, aquí generarías un token JWT o una sesión
        return jsonify({"message": "Inicio de sesión exitoso", "user": {"username": user_data["username"], "email": email}}), 200
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

# --- Ejecutar la aplicación Flask ---
if __name__ == '__main__':
    app.run(debug=True, port=5000) # Ejecutar en el puerto 5000
