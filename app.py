import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('HUBSPOT_ACCESS_TOKEN')
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'}

# --- CONFIGURACIÓN TÉCNICA FINAL ---
OBJETO_EQUIPOS = "p49651985_equipos" 
PROP_TICKET_SN = "numero_de_serie" 
PROP_EQUIPO_SN = "n_mero_de_serie" 
# ------------------------------------

@app.route('/webhook', methods=['POST'])
def hubspot_webhook():
    data = request.json
    for event in data:
        ticket_id = event.get('objectId')
        prop_name = event.get('propertyName')
        sn_value = event.get('propertyValue')

        if prop_name == PROP_TICKET_SN and sn_value:
            vincular_equipo(ticket_id, sn_value)

    return jsonify({"status": "ok"}), 200

def vincular_equipo(ticket_id, sn_value):
    # 1. Buscar el Equipo
    search_url = f"https://api.hubapi.com/crm/v3/objects/{OBJETO_EQUIPOS}/search"
    search_body = {
        "filterGroups": [{"filters": [{"propertyName": PROP_EQUIPO_SN, "operator": "EQ", "value": sn_value}]}]
    }
    
    resp = requests.post(search_url, headers=HEADERS, json=search_body)
    results = resp.json().get('results', [])

    if results:
        equipo_id = results[0]['id']
        print(f"✅ Equipo encontrado: {equipo_id}. Asociando...")
        
        # 2. EL CAMBIO MÁGICO: Usamos la API v4 con 'default'
        # Esto evita tener que saber el nombre interno de la asociación
        assoc_url = f"https://api.hubapi.com/crm/v4/objects/tickets/{ticket_id}/associations/default/{OBJETO_EQUIPOS}/{equipo_id}"
        
        r_assoc = requests.put(assoc_url, headers=HEADERS)
        
        if r_assoc.status_code in [200, 201]:
            print(f"🔥 ¡LOGRADO! Ticket {ticket_id} vinculado a Equipo {equipo_id}")
        else:
            print(f"❌ Error final de asociación: {r_assoc.text}")
    else:
        print(f"⚠️ No se encontró el equipo con SN: {sn_value}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)