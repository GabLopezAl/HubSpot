import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('HUBSPOT_ACCESS_TOKEN')
HEADERS = {'Authorization': f'Bearer {ACCESS_TOKEN}', 'Content-Type': 'application/json'}

# --- REVISA ESTOS DOS ---
OBJETO_EQUIPOS = "equipos" 
# Vamos a probar con 'numero_de_serie' que es lo que se ve en tu suscripción
PROP_NUM_SERIE = "numero_de_serie" 
# ------------------------

@app.route('/webhook', methods=['POST'])
def hubspot_webhook():
    data = request.json
    # ESTO ES CLAVE: Veremos en Render qué nos manda HubSpot exactamente
    print(f"DEBUG - Datos recibidos: {data}")

    for event in data:
        ticket_id = event.get('objectId')
        prop_name = event.get('propertyName')
        new_value = event.get('propertyValue')
        
        print(f"DEBUG - Procesando Propiedad: {prop_name} con Valor: {new_value}")

        # Aquí es donde fallaba: si prop_name no es EXACTO, no entra.
        if prop_name == PROP_NUM_SERIE and new_value:
            vincular_equipo(ticket_id, new_value)

    return jsonify({"status": "ok"}), 200

def vincular_equipo(ticket_id, sn_value):
    print(f"Buscando equipo con SN: {sn_value}...")
    search_url = f"https://api.hubapi.com/crm/v3/objects/{OBJETO_EQUIPOS}/search"
    search_body = {
        "filterGroups": [{"filters": [{"propertyName": PROP_NUM_SERIE, "operator": "EQ", "value": sn_value}]}]
    }
    
    r_search = requests.post(search_url, headers=HEADERS, json=search_body)
    results = r_search.json().get('results', [])

    if results:
        equipo_id = results[0]['id']
        print(f"Equipo encontrado! ID: {equipo_id}. Asociando...")
        
        # Intentamos la asociación directa
        assoc_url = f"https://api.hubapi.com/crm/v3/objects/tickets/{ticket_id}/associations/{OBJETO_EQUIPOS}/{equipo_id}/ticket_to_equipo"
        r_assoc = requests.put(assoc_url, headers=HEADERS)
        
        if r_assoc.status_code in [200, 201]:
            print(f"✅ Éxito total: Ticket {ticket_id} unido a Equipo {equipo_id}")
        else:
            print(f"❌ Error API Asociación: {r_assoc.text}")
    else:
        print(f"⚠️ No se encontró equipo con SN {sn_value} en el objeto {OBJETO_EQUIPOS}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)