import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('HUBSPOT_ACCESS_TOKEN')
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'}

OBJETO_EQUIPOS = "equipos" 
PROP_TICKET_SN = "numero_de_serie" 
PROP_EQUIPO_SN = "n_mero_de_serie" 

@app.route('/webhook', methods=['POST'])
def hubspot_webhook():
    data = request.json
    print(f"DEBUG - Datos recibidos: {data}")

    for event in data:
        ticket_id = event.get('objectId')
        prop_name = event.get('propertyName')
        sn_value = event.get('propertyValue')

        if prop_name == PROP_TICKET_SN and sn_value:
            print(f"Buscando equipo con SN: {sn_value} en la propiedad {PROP_EQUIPO_SN}")
            vincular_equipo(ticket_id, sn_value)

    return jsonify({"status": "ok"}), 200

def vincular_equipo(ticket_id, sn_value):
    search_url = f"https://api.hubapi.com/crm/v3/objects/{OBJETO_EQUIPOS}/search"
    search_body = {
        "filterGroups": [{
            "filters": [{
                "propertyName": PROP_EQUIPO_SN,
                "operator": "EQ",
                "value": sn_value
            }]
        }]
    }
    
    r_search = requests.post(search_url, headers=HEADERS, json=search_body)
    search_data = r_search.json()
    
    if r_search.status_code != 200:
        print(f"❌ Error en búsqueda (API): {search_data}")
        return

    results = search_data.get('results', [])

    if results:
        equipo_id = results[0]['id']
        print(f"✅ Equipo encontrado! ID: {equipo_id}. Asociando...")
        
        # Intentamos asociar
        assoc_url = f"https://api.hubapi.com/crm/v3/objects/tickets/{ticket_id}/associations/{OBJETO_EQUIPOS}/{equipo_id}/ticket_to_equipo"
        r_assoc = requests.put(assoc_url, headers=HEADERS)
        
        if r_assoc.status_code in [200, 201]:
            print(f"🔥 ÉXITO: Ticket {ticket_id} vinculado a Equipo {equipo_id}")
        else:
            print(f"❌ Error al asociar: {r_assoc.text}")
    else:
        print(f"⚠️ No se encontró equipo con SN {sn_value} usando {PROP_EQUIPO_SN}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)