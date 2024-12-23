import requests
import logging
import time
import statistics

# API-Football Config
API_KEY = "c0a61de33419f00ac2e87f119cb25ee4"  # Inserisci la tua chiave API-Football qui
BASE_URL = "https://v3.football.api-sports.io/"
HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY,
}

def is_api_response_valid(response_json):
    """Verifica se la risposta API è valida."""
    if "errors" in response_json and response_json["errors"]:
        return False
    if "message" in response_json and "limit" in response_json["message"].lower():
        return False
    return True

def make_request_with_retry(url, headers, retries=3, delay=2):
    """Effettua una richiesta con tentativi multipli e verifica il contenuto della risposta."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response_json = response.json()

            # Verifica se la risposta è valida
            if not is_api_response_valid(response_json):
                logging.error("Risposta API non valida: limite raggiunto o altro errore.")
                return {"error": "API limit exceeded or invalid response"}

            return response
        except requests.exceptions.RequestException as e:
            logging.error(f"Errore nella richiesta API (tentativo {attempt + 1}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise

# Funzione per ottenere le partite di una squadra
def get_team_matches(team_name):
    try:
        logging.info(f"Ricerca squadra: {team_name}")
        response = make_request_with_retry(f"{BASE_URL}teams?search={team_name}", HEADERS)
        if "error" in response:  # Gestisce il limite API o risposta invalida
            return {"error": "API limit exceeded or invalid response"}
        
        team_data = response.json()
        if team_data['results'] > 0:
            team_id = team_data['response'][0]['team']['id']
            logging.info(f"ID squadra trovato: {team_id}")
            fixtures_response = make_request_with_retry(f"{BASE_URL}fixtures?team={team_id}&next=5", HEADERS)
            if "error" in fixtures_response:
                return {"error": "API limit exceeded or invalid response"}
            return fixtures_response.json().get("response", [])
        else:
            logging.info("Nessuna squadra trovata.")
            return []
    except Exception as e:
        logging.error(f"Errore nell'API: {e}")
        return []

# Funzione per ottenere statistiche primo tempo
def get_first_half_stats(team_id):
    try:
        print(f"[DEBUG] Statistiche primo tempo per Team ID: {team_id}")
        response = requests.get(f"{BASE_URL}fixtures?team={team_id}&last=10", headers=HEADERS)
        fixtures = response.json().get("response", [])
        goals_first_half = []
        over_1_5_first_half = 0

        for match in fixtures:
            stats = match.get("score", {}).get("halftime", {})
            if stats:
                home_goals = stats.get("home", 0) or 0
                away_goals = stats.get("away", 0) or 0
                total_goals = home_goals + away_goals
                goals_first_half.append(total_goals)

                if total_goals > 1.5:
                    over_1_5_first_half += 1

        avg_goals = statistics.mean(goals_first_half) if goals_first_half else 0
        over_1_5_percentage = (over_1_5_first_half / len(goals_first_half)) * 100 if goals_first_half else 0

        print(f"[DEBUG] Statistiche calcolate: {avg_goals} avg goals, {over_1_5_percentage}% over 1.5")
        return avg_goals, over_1_5_percentage
    except Exception as e:
        print(f"[ERROR] Errore nell'API: {e}")
        return 0, 0

def get_h2h_stats(team1_id, team2_id):
    try:
        logging.info(f"Recupero statistiche H2H tra {team1_id} e {team2_id}")
        response = requests.get(f"{BASE_URL}fixtures/headtohead?h2h={team1_id}-{team2_id}", headers=HEADERS)
        h2h_data = response.json().get("response", [])

        if not h2h_data:
            logging.info("Nessuna partita H2H trovata.")
            return {
                "games_played": 0,
                "h2h_avg_goals": 0.0,
                "h2h_over_1_5": 0.0
            }

        total_goals_first_half = 0
        over_1_5_first_half_count = 0

        for match in h2h_data:
            halftime = match.get("score", {}).get("halftime", {})
            home_ht = halftime.get("home", 0) or 0
            away_ht = halftime.get("away", 0) or 0

            logging.debug(f"Valori halftime: home={home_ht}, away={away_ht}")

            total_goals = home_ht + away_ht
            total_goals_first_half += total_goals

            if total_goals > 1.5:
                over_1_5_first_half_count += 1

        games_played = len(h2h_data)
        h2h_avg_goals = total_goals_first_half / games_played if games_played > 0 else 0.0
        h2h_over_1_5 = (over_1_5_first_half_count / games_played) * 100 if games_played > 0 else 0.0

        return {
            "games_played": games_played,
            "h2h_avg_goals": h2h_avg_goals,
            "h2h_over_1_5": h2h_over_1_5
        }
    except Exception as e:
        logging.error(f"Errore durante il recupero delle statistiche H2H: {e}")
        return {
            "games_played": 0,
            "h2h_avg_goals": 0.0,
            "h2h_over_1_5": 0.0
        }

import functools
# Cache per i risultati già calcolati
cache = {}

def calculate_probability(match_id):
    if match_id in cache:
        logging.info(f"Utilizzo dei dati in cache per Match ID: {match_id}")
        return cache[match_id]

    try:
        logging.info(f"Calcolo probabilità per Match ID: {match_id}")
        response = requests.get(f"{BASE_URL}fixtures?id={match_id}", headers=HEADERS)
        if "error" in response:
            return 0, {}

        fixture_data = response.json().get("response", [])
        if not fixture_data:
            logging.error("Nessuna informazione sulla partita trovata.")
            return 0, {}

        fixture_data = fixture_data[0]
        home_team = fixture_data["teams"]["home"]["name"]
        away_team = fixture_data["teams"]["away"]["name"]
        home_team_id = fixture_data["teams"]["home"]["id"]
        away_team_id = fixture_data["teams"]["away"]["id"]

        # Statistiche
        home_avg_goals, home_over_1_5 = get_first_half_stats(home_team_id)
        away_avg_goals, away_over_1_5 = get_first_half_stats(away_team_id)
        h2h_stats = get_h2h_stats(home_team_id, away_team_id)

        logging.info(f"Statistiche H2H: {h2h_stats}")

        # Combina i dati
        details = {
            "home_team": home_team,
            "away_team": away_team,
            "home_avg_goals": home_avg_goals,
            "away_avg_goals": away_avg_goals,
            "games_played": h2h_stats["games_played"],
            "h2h_avg_goals": h2h_stats["h2h_avg_goals"],
            "h2h_over_1_5": h2h_stats["h2h_over_1_5"]
        }
        logging.debug(f"Dettagli calcolati: {details}")

        # Calcolo della probabilità
        combined_avg_goals = (home_avg_goals + away_avg_goals + h2h_stats["h2h_avg_goals"]) / 3
        combined_over_1_5 = (home_over_1_5 + away_over_1_5 + h2h_stats["h2h_over_1_5"]) / 3
        probability = (combined_avg_goals / 1.5) * combined_over_1_5

        # Salva nel cache
        cache[match_id] = (probability, details)
        return min(probability, 100), details
    except Exception as e:
        logging.error(f"Errore durante il calcolo della probabilità: {e}")
        return 0, {}