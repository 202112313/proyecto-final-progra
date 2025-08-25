import os
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import random
import smtplib
from email.mime.text import MIMEText
from flask_cors import CORS 
import mysql.connector
import requests 

app = Flask(__name__)
CORS(app) 

# --- Configuración de la Base de Datos MySQL ---
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",           
        password="12345678duvanm",     
        database="ProyectoBootcamp" 
    )
    cursor = db.cursor(dictionary=True)
    print("Conexión a la base de datos MySQL exitosa.")
except mysql.connector.Error as err:
    print(f"Error al conectar a la base de datos MySQL: {err}")
    db = None
    cursor = None
         
# --- Clave API de Alpha Vantage ---
ALPHA_VANTAGE_API_KEY = "B6WLT43VEKA4J6RW"

# Mapeo de tus claves de commodities a los símbolos de Alpha Vantage
alpha_vantage_symbols = {
    "oro": "GOLD",
    "petroleo": "WTI", 
    "cobre": "COPPER",                 
    "plata": "SILVER",
    "niquel": "NICKEL",
    "litio": "LITHIUM",
    "carbon": "COAL",
    "gasnatural": "NATGAS",
    "hierro": "IRON",
    "aluminio": "ALUMINUM",
    "silicio": "SILICON",
    "litio": "LITHIUM",
    "cobalto": "COBALT",
    "niquel": "NICKEL"
}

# --- Datos de commodities (simulados)
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
    },
    
    "niquel": {
        "id": 5,
        "name": "Níquel",
        "symbol": "NI",
        "description": "Metal estratégico usado en baterías y acero inoxidable",
        "icon_url": "https://placehold.co/40x40/blue/white?text=NI",
        "current_price": 21.50,
        "change": -0.3,
        "change_amount": -0.06,
        "high": 21.80,
        "low": 21.40,
        "history": {
        '1D': [21.60, 21.55, 21.50, 21.45, 21.55, 21.50],
        '1S': [21.00, 21.20, 21.30, 21.40, 21.60, 21.50],
        '1M': [20.00, 20.50, 20.80, 21.20, 21.40, 21.50],
        '3M': [19.50, 20.00, 20.50, 20.80, 21.20, 21.50],
        '1A': [18.00, 19.00, 19.50, 20.50, 21.00, 21.50],
        '5A': [15.00, 16.50, 17.50, 19.00, 20.50, 21.50]
    },
    "news": [
        {"title": "La demanda de níquel crece por la producción de baterías", "source": "Reuters", "time": "Hace 3 horas", "snippet": "El auge de los autos eléctricos impulsa el mercado del níquel...", "url": "https://example.com/news/niquel-baterias"},
        {"title": "Nuevas minas en Indonesia aumentarán la oferta de níquel", "source": "Bloomberg", "time": "Ayer", "snippet": "Se espera que Indonesia duplique su producción de níquel en los próximos años...", "url": "https://example.com/news/niquel-indonesia"}
    ]
},

"litio": {
    "id": 6,
    "name": "Litio",
    "symbol": "LI",
    "description": "Elemento clave en la producción de baterías de ion-litio",
    "icon_url": "https://placehold.co/40x40/green/white?text=LI",
    "current_price": 73.20,
    "change": 1.1,
    "change_amount": 0.8,
    "high": 74.50,
    "low": 72.00,
    "history": {
        '1D': [72.50, 72.80, 73.00, 73.20, 73.50, 73.20],
        '1S': [70.00, 71.20, 72.00, 73.00, 73.50, 73.20],
        '1M': [68.00, 69.50, 71.00, 72.50, 73.00, 73.20],
        '3M': [65.00, 67.00, 69.00, 71.50, 72.80, 73.20],
        '1A': [55.00, 60.00, 65.00, 70.00, 72.00, 73.20],
        '5A': [30.00, 40.00, 50.00, 60.00, 70.00, 73.20]
    },
    "news": [
        {"title": "El litio se convierte en recurso estratégico", "source": "El País", "time": "Hoy", "snippet": "El auge de los autos eléctricos aumenta la demanda global de litio...", "url": "https://example.com/news/litio-estrategico"},
        {"title": "Chile y Argentina lideran la producción de litio", "source": "Financial Times", "time": "Hace 2 días", "snippet": "Sudamérica concentra más del 60% de las reservas mundiales de litio...", "url": "https://example.com/news/litio-latam"}
    ]
},

"carbon": {
    "id": 7,
    "name": "Carbón",
    "symbol": "COAL",
    "description": "Combustible fósil utilizado en generación eléctrica y acero",
    "icon_url": "https://placehold.co/40x40/black/white?text=C",
    "current_price": 145.80,
    "change": -2.0,
    "change_amount": -3.0,
    "high": 150.00,
    "low": 144.00,
    "history": {
        '1D': [148.00, 147.00, 146.50, 146.00, 145.80, 145.80],
        '1S': [150.00, 149.00, 148.00, 147.50, 146.50, 145.80],
        '1M': [160.00, 155.00, 150.00, 148.00, 146.00, 145.80],
        '3M': [170.00, 165.00, 160.00, 155.00, 150.00, 145.80],
        '1A': [180.00, 175.00, 170.00, 160.00, 150.00, 145.80],
        '5A': [200.00, 190.00, 180.00, 170.00, 160.00, 145.80]
    },
    "news": [
        {"title": "El carbón sigue siendo clave en Asia", "source": "BBC", "time": "Hoy", "snippet": "China e India siguen dependiendo del carbón para su matriz energética...", "url": "https://example.com/news/carbon-asia"},
        {"title": "Europa reduce su consumo de carbón", "source": "DW", "time": "Ayer", "snippet": "Las políticas de transición energética buscan reemplazar el carbón...", "url": "https://example.com/news/carbon-europa"}
    ]
},

"gasnatural": {
    "id": 8,
    "name": "Gas Natural",
    "symbol": "NG",
    "description": "Fuente de energía fósil usada en calefacción y electricidad",
    "icon_url": "https://placehold.co/40x40/orange/white?text=NG",
    "current_price": 3.25,
    "change": 0.2,
    "change_amount": 0.07,
    "high": 3.40,
    "low": 3.20,
    "history": {
        '1D': [3.20, 3.22, 3.24, 3.26, 3.30, 3.25],
        '1S': [3.00, 3.05, 3.10, 3.20, 3.28, 3.25],
        '1M': [2.80, 2.90, 3.00, 3.10, 3.20, 3.25],
        '3M': [2.50, 2.70, 2.90, 3.10, 3.20, 3.25],
        '1A': [2.00, 2.20, 2.50, 2.80, 3.00, 3.25],
        '5A': [1.50, 2.00, 2.50, 2.80, 3.10, 3.25]
    },
    "news": [
        {"title": "El precio del gas natural sube en invierno", "source": "Reuters", "time": "Hoy", "snippet": "La demanda de calefacción en el hemisferio norte aumenta el precio del gas...", "url": "https://example.com/news/gas-invierno"},
        {"title": "Nuevos yacimientos de gas en el Mediterráneo", "source": "Bloomberg", "time": "Hace 3 días", "snippet": "Descubrimientos recientes aumentan las reservas disponibles de gas natural...", "url": "https://example.com/news/gas-mediterraneo"}
    ]
},
"hierro": {
    "id": 5,
    "name": "Hierro",
    "symbol": "FE",
    "description": "Metal base esencial para la producción de acero en construcción e infraestructura",
    "icon_url": "https://placehold.co/40x40/gray/white?text=FE",
    "current_price": 120.50,
    "change": 0.8,
    "change_amount": 1.0,
    "high": 122.00,
    "low": 119.00,
    "history": {
        "1D": [120.0, 120.5, 121.0, 121.5, 121.0, 120.5],
        "1S": [118.0, 119.0, 119.5, 120.0, 121.0, 120.5],
        "1M": [110.0, 113.0, 115.0, 118.0, 120.0, 120.5],
        "3M": [105.0, 108.0, 112.0, 115.0, 118.0, 120.5],
        "1A": [90.0, 95.0, 100.0, 110.0, 115.0, 120.5],
        "5A": [70.0, 80.0, 90.0, 100.0, 110.0, 120.5]
    },
    "news": [
        {
            "title": "El hierro impulsa el sector de la construcción",
            "source": "Reuters",
            "time": "Hoy",
            "snippet": "El hierro sigue siendo clave en proyectos de infraestructura globales...",
            "url": "https://example.com/news/hierro-construccion"
        }
    ]
},

"aluminio": {
    "id": 6,
    "name": "Aluminio",
    "symbol": "AL",
    "description": "Metal ligero utilizado en construcción, transporte y empaques",
    "icon_url": "https://placehold.co/40x40/silver/black?text=AL",
    "current_price": 2450.0,
    "change": -0.5,
    "change_amount": -12.0,
    "high": 2500.0,
    "low": 2440.0,
    "history": {
        "1D": [2460, 2455, 2450, 2445, 2455, 2450],
        "1S": [2400, 2420, 2440, 2460, 2470, 2450],
        "1M": [2300, 2350, 2380, 2420, 2440, 2450],
        "3M": [2200, 2250, 2300, 2380, 2420, 2450],
        "1A": [2000, 2100, 2200, 2300, 2400, 2450],
        "5A": [1500, 1700, 1900, 2100, 2300, 2450]
    },
    "news": [
        {
            "title": "El aluminio gana protagonismo en la construcción verde",
            "source": "Bloomberg",
            "time": "Ayer",
            "snippet": "El aluminio reciclado reduce la huella de carbono en nuevas edificaciones...",
            "url": "https://example.com/news/aluminio-verde"
        }
    ]
},

"silicio": {
    "id": 7,
    "name": "Silicio",
    "symbol": "SI",
    "description": "Elemento fundamental en la fabricación de paneles solares y semiconductores",
    "icon_url": "https://placehold.co/40x40/orange/white?text=SI",
    "current_price": 1500.0,
    "change": 2.0,
    "change_amount": 30.0,
    "high": 1520.0,
    "low": 1470.0,
    "history": {
        "1D": [1480, 1490, 1500, 1510, 1520, 1500],
        "1S": [1400, 1430, 1460, 1480, 1500, 1500],
        "1M": [1300, 1350, 1400, 1450, 1480, 1500],
        "3M": [1200, 1250, 1300, 1400, 1450, 1500],
        "1A": [1000, 1100, 1200, 1300, 1400, 1500],
        "5A": [700, 850, 1000, 1200, 1400, 1500]
    },
    "news": [
        {
            "title": "El silicio impulsa la revolución solar",
            "source": "TechCrunch",
            "time": "Hace 3 días",
            "snippet": "Los precios del silicio suben por la alta demanda de paneles solares y chips...",
            "url": "https://example.com/news/silicio-solar"
        }
    ]
},

"litio": {
    "id": 8,
    "name": "Litio",
    "symbol": "LI",
    "description": "Elemento clave en la producción de baterías de ion-litio",
    "icon_url": "https://placehold.co/40x40/green/white?text=LI",
    "current_price": 73.20,
    "change": 1.1,
    "change_amount": 0.8,
    "high": 74.50,
    "low": 72.00,
    "history": {
        "1D": [72.50, 72.80, 73.00, 73.20, 73.50, 73.20],
        "1S": [70.00, 71.20, 72.00, 73.00, 73.50, 73.20],
        "1M": [68.00, 69.50, 71.00, 72.50, 73.00, 73.20],
        "3M": [65.00, 67.00, 69.00, 71.50, 72.80, 73.20],
        "1A": [55.00, 60.00, 65.00, 70.00, 72.00, 73.20],
        "5A": [30.00, 40.00, 50.00, 60.00, 70.00, 73.20]
    },
    "news": [
        {
            "title": "El litio se convierte en recurso estratégico",
            "source": "El País",
            "time": "Hoy",
            "snippet": "El auge de los autos eléctricos aumenta la demanda global de litio...",
            "url": "https://example.com/news/litio-estrategico"
        }
    ]
},

"cobalto": {
    "id": 9,
    "name": "Cobalto",
    "symbol": "CO",
    "description": "Mineral usado en baterías, superaleaciones y tecnología médica",
    "icon_url": "https://placehold.co/40x40/blue/white?text=CO",
    "current_price": 45.80,
    "change": -0.5,
    "change_amount": -0.2,
    "high": 46.20,
    "low": 45.50,
    "history": {
        "1D": [46.0, 45.9, 45.8, 45.7, 45.9, 45.8],
        "1S": [44.5, 45.0, 45.5, 46.0, 46.2, 45.8],
        "1M": [42.0, 43.0, 44.0, 45.0, 45.5, 45.8],
        "3M": [38.0, 40.0, 42.0, 44.0, 45.0, 45.8],
        "1A": [30.0, 34.0, 38.0, 42.0, 45.0, 45.8],
        "5A": [20.0, 25.0, 30.0, 35.0, 40.0, 45.8]
    },
    "news": [
        {
            "title": "El cobalto sigue siendo crítico en la industria de baterías",
            "source": "Financial Times",
            "time": "Ayer",
            "snippet": "El suministro de cobalto depende en gran parte de África central...",
            "url": "https://example.com/news/cobalto-baterias"
        }
    ]
},

"niquel": {
    "id": 10,
    "name": "Níquel",
    "symbol": "NI",
    "description": "Metal estratégico usado en baterías y acero inoxidable",
    "icon_url": "https://placehold.co/40x40/blue/white?text=NI",
    "current_price": 21.50,
    "change": -0.3,
    "change_amount": -0.06,
    "high": 21.80,
    "low": 21.40,
    "history": {
        "1D": [21.60, 21.55, 21.50, 21.45, 21.55, 21.50],
        "1S": [21.00, 21.20, 21.30, 21.40, 21.60, 21.50],
        "1M": [20.00, 20.50, 20.80, 21.20, 21.40, 21.50],
        "3M": [19.50, 20.00, 20.50, 20.80, 21.20, 21.50],
        "1A": [18.00, 19.00, 19.50, 20.50, 21.00, 21.50],
        "5A": [15.00, 16.50, 17.50, 19.00, 20.50, 21.50]
    },
    "news": [
        {
            "title": "La demanda de níquel crece por la producción de baterías",
            "source": "Reuters",
            "time": "Hace 3 horas",
            "snippet": "El auge de los autos eléctricos impulsa el mercado del níquel...",
            "url": "https://example.com/news/niquel-baterias"
        }
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

# --- Base de datos de usuarios simulada (para registro/login) ---
users_db = {} # Inicializar como un diccionario vacío

# --- Funciones auxiliares para Alpha Vantage ---
def get_alpha_vantage_quote(av_symbol):
    """
    Obtiene la cotización global de un símbolo de Alpha Vantage.
    Retorna un diccionario con los datos o None si falla.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={av_symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status() # Lanza un error para códigos de estado HTTP malos (4xx o 5xx)
        data = response.json()

        if "Global Quote" in data:
            quote = data["Global Quote"]
            return {
                "current_price": float(quote.get('05. price')),
                "change": float(quote.get('09. change')),
                "change_amount": float(quote.get('09. change')), # Alpha Vantage solo da 'change', no 'change_amount' directo
                "high": float(quote.get('03. high')),
                "low": float(quote.get('04. low'))
            }
        elif "Error Message" in data:
            print(f"Error de Alpha Vantage para {av_symbol}: {data['Error Message']}")
            return None
        elif "Note" in data:
            print(f"Nota de Alpha Vantage (límite de API?): {data['Note']}")
            return None
        else:
            print(f"Respuesta inesperada de Alpha Vantage para {av_symbol}: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión con Alpha Vantage para {av_symbol}: {e}")
        return None
    except (ValueError, TypeError) as e:
        print(f"Error al procesar datos de Alpha Vantage para {av_symbol}: {e}")
        return None

# --- Rutas de la API ---

@app.route('/')
def home():
    return "Backend de Commodity Trader funcionando. ¡Conéctate desde tu frontend!"

# 1. API para obtener precios y datos de commodities
@app.route('/api/commodities', methods=['GET'])
def get_commodities():
    """
    Retorna una lista de todas las commodities disponibles con sus datos actuales,
    intentando obtener precios en tiempo real de Alpha Vantage como primera opción.
    """
    commodities_list = []
    for key, data in commodities_db.items():
        commodity_info = data.copy() # Copia los datos simulados
        
        # Intentar obtener datos en tiempo real de Alpha Vantage
        av_symbol = alpha_vantage_symbols.get(key)
        if av_symbol:
            realtime_data = get_alpha_vantage_quote(av_symbol)
            if realtime_data:
                # Actualizar los campos con los datos de Alpha Vantage
                commodity_info["current_price"] = realtime_data["current_price"]
                commodity_info["change"] = realtime_data["change"]
                commodity_info["change_amount"] = realtime_data["change_amount"]
                commodity_info["high"] = realtime_data["high"]
                commodity_info["low"] = realtime_data["low"]
                print(f"Datos de {key} actualizados con Alpha Vantage.")
            else:
                print(f"No se pudieron obtener datos de Alpha Vantage para {key}. Usando datos simulados.")
        else:
            print(f"No hay mapeo de Alpha Vantage para {key}. Usando datos simulados.")

        # Formatear la salida para el frontend
        commodities_list.append({
            "key": key,
            "name": commodity_info["name"],
            "symbol": commodity_info["symbol"],
            "icon_url": commodity_info["icon_url"],
            "current_price": round(commodity_info["current_price"], 2),
            "change": round(commodity_info["change"], 2),
            "high": round(commodity_info["high"], 2),
            "low": round(commodity_info["low"], 2)
        })
    return jsonify(commodities_list)

@app.route('/api/commodity/<string:commodity_key>', methods=['GET'])
def get_commodity_details(commodity_key):
    """
    Retorna los detalles completos de una commodity específica, incluyendo historial y noticias.
    Intenta actualizar el precio actual con Alpha Vantage.
    """
    commodity_data = commodities_db.get(commodity_key)
    if not commodity_data:
        return jsonify({"error": "Commodity no encontrada"}), 404
    
    # Crear una copia para no modificar el original en commodities_db
    details_to_return = commodity_data.copy()

    # Intentar obtener el precio actual de Alpha Vantage para esta commodity
    av_symbol = alpha_vantage_symbols.get(commodity_key)
    if av_symbol:
        realtime_data = get_alpha_vantage_quote(av_symbol)
        if realtime_data:
            details_to_return["current_price"] = realtime_data["current_price"]
            details_to_return["change"] = realtime_data["change"]
            details_to_return["change_amount"] = realtime_data["change_amount"]
            details_to_return["high"] = realtime_data["high"]
            details_to_return["low"] = realtime_data["low"]
            print(f"Detalles de {commodity_key} actualizados con Alpha Vantage.")
        else:
            print(f"No se pudieron obtener datos de Alpha Vantage para los detalles de {commodity_key}. Usando datos simulados.")
    else:
        print(f"No hay mapeo de Alpha Vantage para los detalles de {commodity_key}. Usando datos simulados.")

    # Redondear los valores numéricos para la respuesta
    details_to_return["current_price"] = round(details_to_return["current_price"], 2)
    details_to_return["change"] = round(details_to_return["change"], 2)
    details_to_return["change_amount"] = round(details_to_return["change_amount"], 2)
    details_to_return["high"] = round(details_to_return["high"], 2)
    details_to_return["low"] = round(details_to_return["low"], 2)

    return jsonify(details_to_return)

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
