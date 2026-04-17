import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('HUBSPOT_ACCESS_TOKEN')
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'}

# --- CONFIGURACIÓN TÉCNICA FINAL ---
# Usamos el nombre calificado con tu Portal ID
OBJETO_EQUIPOS = "p49651985_equipos" 

# Nombres de propiedades confirmados en tus logs y capturas
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

        # Verificamos cambio en el ticket
        if prop_name == PROP_TICKET_SN and sn_value:
            print(f"DEBUG: Buscando Equipo con SN {sn_value} en {OBJETO_EQUIPOS}")
            vincular_equipo(ticket_id, sn_value)

    return jsonify({"status": "ok"}), 200

def vincular_equipo(ticket_id, sn_value):
    # 1. Buscar el Equipo
    search_url = f"https://api.hubapi.com/crm/v3/objects/{OBJETO_EQUIPOS}/search"
    search_body = {
        "filterGroups": [{"filters": [{"propertyName": PROP_EQUIPO_SN, "operator": "EQ", "value": sn_value}]}]
    }
    
    resp = requests.post(search_url, headers=HEADERS, json=search_body)
    
    if resp.status_code != 200:
        print(f"❌ ERROR EN BÚSQUEDA: {resp.text}")
        return

    results = resp.json().get('results', [])
    if results:
        equipo_id = results[0]['id']
        print(f"✅ ¡Equipo encontrado! ID: {equipo_id}. Intentando asociar...")
        
        # 2. Asociar (Usamos el mismo nombre calificado para el objeto destino)
        assoc_url = f"https://api.hubapi.com/crm/v3/objects/tickets/{ticket_id}/associations/{OBJETO_EQUIPOS}/{equipo_id}/ticket_to_equipo"
        
        r_assoc = requests.put(assoc_url, headers=HEADERS)
        
        if r_assoc.status_code in [200, 201]:
            print(f"🔥 ¡ÉXITO TOTAL! Ticket {ticket_id} vinculado a Equipo {equipo_id}")
        else:
            print(f"❌ ERROR EN ASOCIACIÓN: {r_assoc.text}")
    else:
        print(f"⚠️ No se encontró ningún equipo con SN: {sn_value}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)