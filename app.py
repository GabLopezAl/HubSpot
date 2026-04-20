import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('HUBSPOT_ACCESS_TOKEN')
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'}

OBJETO_EQUIPOS = "p49651985_equipos" 
PROP_TICKET_NS = "numero_de_serie" 
PROP_EQUIPO_NS = "n_mero_de_serie" 

@app.route('/webhook', methods=['POST'])
def hubspot_webhook():
    datos = request.json
    eventos = datos if isinstance(datos, list) else [datos]

    for evento in eventos:
        ticket_id = evento.get('objectId')
        prop_name = evento.get('propertyName')
        ns_value = evento.get('propertyValue')

        if prop_name == PROP_TICKET_NS and ns_value:
            lista_ns = [ns.strip() for ns in ns_value.split(',') if ns.strip()]
            asociados_actuales = obtener_asociaciones_actuales(ticket_id)
            
            for ns in lista_ns:
                vincular_equipo(ticket_id, ns, asociados_actuales)

    return jsonify({"status": "ok"}), 200

def obtener_asociaciones_actuales(ticket_id):
    url = f"https://api.hubapi.com/crm/v4/objects/tickets/{ticket_id}/associations/{OBJETO_EQUIPOS}"
    try:
        respuesta = requests.get(url, headers=HEADERS)
        if respuesta.status_code == 200:
            # Retornamos una lista de IDs de equipos ya vinculados
            return [str(r['toObjectId']) for r in respuesta.json().get('results', [])]
    except Exception as e:
        print(f"Error consultando asociaciones: {e}")
    return []

def vincular_equipo(ticket_id, ns_value, asociados_actuales):
    url_search = f"https://api.hubapi.com/crm/v3/objects/{OBJETO_EQUIPOS}/search"
    busqueda = {
        "filterGroups": [{"filters": [{"propertyName": PROP_EQUIPO_NS, "operator": "EQ", "value": ns_value}]}]
    }
    
    res_search = requests.post(url_search, headers=HEADERS, json=busqueda)
    resultado = res_search.json().get('results', [])

    if resultado:
        equipo_id = str(resultado[0]['id'])
        
        if equipo_id in asociados_actuales:
            print(f"El equipo {ns_value} (ID: {equipo_id}) ya está asociado al Ticket {ticket_id}. Saltando...")
            return

        url_assoc = f"https://api.hubapi.com/crm/v4/objects/tickets/{ticket_id}/associations/default/{OBJETO_EQUIPOS}/{equipo_id}"
        operacion_assoc = requests.put(url_assoc, headers=HEADERS)
        
        # if operacion_assoc.status_code in [200, 201]:
        #     print(f"{ns_value} vinculado a Ticket {ticket_id}")
        # else:
        #     print(f"Error asociando {ns_value}: {operacion_assoc.text}")
    else:
        print(f"No se encontró el equipo con serie: {ns_value}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)