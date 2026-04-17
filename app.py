import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Configuración desde las variables de entorno de Render
ACCESS_TOKEN = os.environ.get('HUBSPOT_ACCESS_TOKEN')
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

# --- VALORES CONFIRMADOS POR TUS CAPTURAS ---
OBJETO_EQUIPOS = "equipos" 
PROP_NUM_SERIE = "n_mero_de_serie" 
# --------------------------------------------

@app.route('/webhook', methods=['POST'])
def hubspot_webhook():
    data = request.json
    if not data:
        return jsonify({"status": "no data"}), 400

    for event in data:
        # Detectamos el cambio en la propiedad n_mero_de_serie
        if event.get('subscriptionType') == 'crm.objects.propertyChange':
            ticket_id = event.get('objectId')
            
            if event.get('propertyName') == PROP_NUM_SERIE:
                sn_value = event.get('propertyValue')
                if sn_value:
                    print(f"Vinculando Ticket {ticket_id} con Equipo SN: {sn_value}")
                    vincular_equipo(ticket_id, sn_value)

    return jsonify({"status": "ok"}), 200

def vincular_equipo(ticket_id, sn_value):
    # 1. Buscar el Equipo por su número de serie
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
        
        # 2. Crear la asociación oficial entre Ticket y Equipo
        # El tipo 'ticket_to_equipo' es el estándar para esta relación
        assoc_url = f"https://api.hubapi.com/crm/v3/objects/tickets/{ticket_id}/associations/{OBJETO_EQUIPOS}/{equipo_id}/ticket_to_equipo"
        
        r_assoc = requests.put(assoc_url, headers=HEADERS)
        
        if r_assoc.status_code in [200, 201]:
            print(f"Éxito: Ticket {ticket_id} asociado a Equipo {equipo_id}")
        else:
            print(f"Error de API: {r_assoc.text}")
    else:
        print(f"⚠️ No se encontró el equipo con SN: {sn_value}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)