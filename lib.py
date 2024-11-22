import requests
import logging
import time
import statistics

# API-Football Config
API_KEY = "YOUR_API_KEY"  # Inserisci la tua chiave API-Football qui
BASE_URL = "https://v3.football.api-sports.io/"
HEADERS = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY,
}

# Funzione per effettuare richieste con retry
def make_request_with_retry(url, headers, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
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
        team_data = response.json()
        if team_data['results'] > 0:
            team_id = team_data['response'][0]['team']['id']
            logging.info(f"ID squadra trovato: {team_id}")
            fixtures_response = make_request_with_retry(f"{BASE_URL}fixtures?team={team_id}&next=5", HEADERS)
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
        logging.info(f"Statistiche primo tempo per Team ID: {team_id}")
        response = make_request_with_retry(f"{BASE_URL}fixtures?team={team_id}&last=10", HEADERS)
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
        logging.info(f"Statistiche calcolate: {avg_goals} avg goals, {over_1_5_percentage}% over 1.5")
        return avg_goals, over_1_5_percentage
    except Exception as e:
        logging.error(f"Errore nell'API: {e}")
        return 0, 0

# Funzione per calcolare probabilità Over 1.5
def calculate_probability(match_id):
    try:
        logging.info(f"Calcolo probabilità per Match ID: {match_id}")
        response = make_request_with_retry(f"{BASE_URL}fixtures?id={match_id}", HEADERS)
        fixture_data = response.json().get("response", [])
        if not fixture_data:
            logging.error("Nessuna informazione sulla partita trovata.")
            return 0, {}

        fixture_data = fixture_data[0]
        home_team = fixture_data["teams"]["home"]["name"]
        away_team = fixture_data["teams"]["away"]["name"]
        home_team_id = fixture_data["teams"]["home"]["id"]
        away_team_id = fixture_data["teams"]["away"]["id"]

        home_avg_goals, home_over_1_5 = get_first_half_stats(home_team_id)
        away_avg_goals, away_over_1_5 = get_first_half_stats(away_team_id)

        combined_avg_goals = (home_avg_goals + away_avg_goals) / 2
        combined_over_1_5 = (home_over_1_5 + away_over_1_5) / 2
        probability = (combined_avg_goals / 1.5) * combined_over_1_5

        details = {
            "home_team": home_team,
            "away_team": away_team,
            "home_avg_goals": home_avg_goals,
            "away_avg_goals": away_avg_goals,
            "home_over_1_5": home_over_1_5,
            "away_over_1_5": away_over_1_5,
        }

        logging.info(f"Dettagli calcolo: {details}")
        return min(probability, 100), details
    except Exception as e:
        logging.error(f"Errore nel calcolo della probabilità: {e}")
        return 0, {}
