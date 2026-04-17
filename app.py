import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuración desde Render
ACCESS_TOKEN = os.environ.get('HUBSPOT_ACCESS_TOKEN')
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

# --- SUSTITUYE ESTO CON TUS DATOS ---
OBJETO_EQUIPOS = "equipos" 
PROP_NUM_SERIE = "n_mero_de_serie" # Verifica este en 'Gestionar propiedades'
# ------------------------------------

@app.route('/webhook', methods=['POST'])
def hubspot_webhook():
    data = request.json
    # HubSpot puede enviar varios eventos en un solo aviso (lista)
    for event in data:
        if event.get('subscriptionType') == 'crm.objects.propertyChange':
            ticket_id = event.get('objectId')
            # Solo actuamos si cambió la propiedad de número de serie
            if event.get('propertyName') == PROP_NUM_SERIE:
                sn_value = event.get('propertyValue')
                if sn_value:
                    vincular_equipo(ticket_id, sn_value)

    return jsonify({"status": "ok"}), 200

def vincular_equipo(ticket_id, sn_value):
    # 1. Buscar el ID del equipo por su SN
    search_url = f"https://api.hubapi.com/crm/v3/objects/{OBJETO_EQUIPOS}/search"
    search_body = {
        "filterGroups": [{
            "filters": [{
                "propertyName": PROP_NUM_SERIE,
                "operator": "EQ",
                "value": sn_value
            }]
        }]
    }
    
    resp = requests.post(search_url, headers=HEADERS, json=search_body)
    results = resp.json().get('results', [])

    if results:
        equipo_id = results[0]['id']
        
        # 2. Crear la asociación (v3 API)
        # El ID de asociación para 'ticket a objeto personalizado' suele ser el 27
        assoc_url = f"https://api.hubapi.com/crm/v3/associations/tickets/{OBJETO_EQUIPOS}/batch/create"
        assoc_body = {
            "inputs": [{
                "from": {"id": ticket_id},
                "to": {"id": equipo_id},
                "type": "ticket_to_custom_object" # Intenta este primero
            }]
        }
        requests.post(assoc_url, headers=HEADERS, json=assoc_body)
        print(f"Ticket {ticket_id} asociado al equipo {sn_value}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)