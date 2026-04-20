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
    for evento in datos:
        ticket_id = evento.get('objectId')
        prop_name = evento.get('propertyName')
        ns_value = evento.get('propertyValue')

        if prop_name == PROP_TICKET_NS and ns_value:
            vincular_equipo(ticket_id, ns_value)

    return jsonify({"status": "ok"}), 200

def vincular_equipo(ticket_id, ns_value):
    ns_limpio = str(ns_value).strip()
    
    url_objeto = f"https://api.hubapi.com/crm/v3/objects/{OBJETO_EQUIPOS}/search"
    
    busqueda = {
        "filterGroups": [{
            "filters": [{
                "propertyName": PROP_EQUIPO_NS, 
                "operator": "EQ", 
                "value": ns_limpio
            }]
        }]
    }
    
    print(f"Intentando buscar equipo con {PROP_EQUIPO_NS} = '{ns_limpio}'")
    
    respuesta = requests.post(url_objeto, headers=HEADERS, json=busqueda)
    
    datos_respuesta = respuesta.json()
    
    if respuesta.status_code != 200:
        print(f"Error en la API de búsqueda: {datos_respuesta}")
        return

    resultado = datos_respuesta.get('results', [])

    if resultado:
        equipo_id = resultado[0]['id']
        print(f"Equipo encontrado ID: {equipo_id}. Vinculando")
        
        url_asociacion = f"https://api.hubapi.com/crm/v4/objects/tickets/{ticket_id}/associations/default/{OBJETO_EQUIPOS}/{equipo_id}"
        operacion_assoc = requests.put(url_asociacion, headers=HEADERS)
        
        if operacion_assoc.status_code in [200, 201]:
            print(f"Ticket {ticket_id} vinculado a equipo {equipo_id}")
        else:
            print(f"Error en asociación: {operacion_assoc.status_code} - {operacion_assoc.text}")
    else:
        print(f"...Equipo no encontrado...")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)