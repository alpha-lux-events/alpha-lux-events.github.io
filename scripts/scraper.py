import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BIN_ID = os.environ.get('JSONBIN_BIN_ID')
API_KEY = os.environ.get('JSONBIN_API_KEY')

def fetch_existing_events():
    """Récupère les événements actuels depuis JSONBin"""
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
    headers = {'X-Master-Key': API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('record', [])
    except Exception as e:
        print(f"Erreur lors de la récupération JSONBin: {e}")
    return []

def scrape_alfi():
    events = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get("https://www.alfi.lu/en-gb/events", headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('.event-item, .card, article'):
                title_el = item.select_one('h2, h3, a.title')
                if title_el:
                    title = title_el.text.strip()
                    events.append({
                        "id": abs(hash(title)) % 1000000,
                        "title": title,
                        "type": "conference",
                        "date": "2027-06-15", # Date par défaut ou extraite
                        "time": "09:00",
                        "location": "Luxembourg",
                        "organizer": "ALFI",
                        "url": "https://www.alfi.lu",
                        "attendees": []
                    })
    except Exception as e:
        print(f"Erreur ALFI: {e}")
    return events

def scrape_abbl():
    events = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = requests.get("https://www.abbl.lu/en/events", headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.select('.event-card, .views-row'):
                title_el = item.select_one('h3, h2, a')
                if title_el and len(title_el.text.strip()) > 5:
                    title = title_el.text.strip()
                    events.append({
                        "id": abs(hash(title)) % 1000000,
                        "title": title,
                        "type": "seminar",
                        "date": "2027-05-10",
                        "time": "09:00",
                        "location": "Luxembourg",
                        "organizer": "ABBL",
                        "url": "https://www.abbl.lu",
                        "attendees": []
                    })
    except Exception as e:
        print(f"Erreur ABBL: {e}")
    return events

def merge_events(existing, new_ones):
    """Fusionne sans écraser les listes 'attendees' des collaborateurs"""
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
    print("Démarrage du scraping multi-sources...")
    existing = fetch_existing_events()
    
    all_new_events = []
    all_new_events.extend(scrape_alfi())
    all_new_events.extend(scrape_abbl())
    
    if all_new_events:
        final_events = merge_events(existing, all_new_events)
        save_to_jsonbin(final_events)
        print(f"Synchronisation terminée. Total événements: {len(final_events)}")
    else:
        print("Aucun événement récupéré lors de cette exécution.")
