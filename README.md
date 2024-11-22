# ⚽ Football Stats Bot 🤖

Un bot Telegram per calcolare la probabilità di **Over 1.5 gol nel primo tempo** per partite di calcio. Il bot utilizza l'API-Football per ottenere statistiche aggiornate e offre una gestione resiliente degli errori.

---

## 📚 Funzionalità
1. **🔍 Ricerca Squadra**: Inserisci il nome di una squadra per visualizzare le prossime partite.
2. **🗂️ Menu Interattivo**: Seleziona una partita da un elenco generato automaticamente.
3. **📊 Analisi Completa**:
   - Media gol segnati nel primo tempo.
   - Percentuale di Over 1.5 gol nel primo tempo.
   - Statistiche sugli scontri diretti (H2H).
4. **🔄 Resilienza**:
   - Ritenta automaticamente in caso di errori API.
   - Gestisce tutte le eccezioni senza interrompere il funzionamento.

---

## 🚀 Come Usare il Bot

### 1️⃣ Prerequisiti
- **Python 3.8+**
- **Chiave API-Football**
  - Registrati su [API-Football](https://www.api-football.com/) e copia la tua chiave API.
- **Token Telegram Bot**
  - Ottieni il token dal [BotFather](https://core.telegram.org/bots#botfather).

### 2️⃣ Installazione
1. Clona il repository:
   ```bash
   git clone https://github.com/<tuo-username>/football-stats-bot.git
   cd football-stats-bot
