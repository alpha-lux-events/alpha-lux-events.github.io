import os
import requests
from bs4 import BeautifulSoup

BIN_ID = os.environ.get('JSONBIN_BIN_ID')
API_KEY = os.environ.get('JSONBIN_API_KEY')

def fetch_existing_events():
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
    headers = {'X-Master-Key': API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('record', [])
    except Exception as e:
        print(f"Erreur lors de la récupération JSONBin: {e}")
    return []

def scrape_events():
    scraped_events = []
    
    # Exemple de scraping ALFI
    try:
        res = requests.get("https://www.alfi.lu/en-gb/events", timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('.event-item, .card-event')[:5]:
                title_elem = item.select_one('h2, h3, .title')
                if title_elem:
                    scraped_events.append({
                        "id": abs(hash(title_elem.text.strip())) % 100000,
                        "title": title_elem.text.strip(),
                        "type": "conference",
                        "date": "2027-06-01",
                        "organizer": "ALFI",
                        "url": "https://www.alfi.lu",
                        "attendees": []
                    })
    except Exception as e:
        print(f"Erreur scraping ALFI: {e}")

    return scraped_events

def merge_events(existing, new_ones):
    map_events = {e['id']: e for e in existing}
    for new_e in new_ones:
        if new_e['id'] in map_events:
            current_attendees = map_events[new_e['id']].get('attendees', [])
            map_events[new_e['id']].update(new_e)
            if current_attendees:
                map_events[new_e['id']]['attendees'] = current_attendees
        else:
            map_events[new_e['id']] = new_e
    return list(map_events.values())

def save_to_jsonbin(events):
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
    headers = {
        'Content-Type': 'application/json',
        'X-Master-Key': API_KEY
    }
    response = requests.put(url, headers=headers, json=events)
    if response.status_code == 200:
        print("Mise à jour réussie sur JSONBin !")
    else:
        print(f"Erreur sauvegarde: {response.text}")

if __name__ == "__main__":
    print("Démarrage du scraping...")
    existing = fetch_existing_events()
    new_data = scrape_events()
    if new_data:
        final_events = merge_events(existing, new_data)
        save_to_jsonbin(final_events)
    else:
        print("Aucun nouvel événement récupéré.")
