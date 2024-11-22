import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from lib import get_team_matches, calculate_probability

# Configura il logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # Salva i log su file
        logging.StreamHandler()          # Mostra i log in console
    ]
)

# Bot Telegram Config
BOT_TOKEN = "7620362203:AAG7kyvMbum0gRkJjYpj-wvpy4s0bXGLaYQ"  # Inserisci il tuo token Telegram qui

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Benvenuto! Inserisci il nome della squadra per iniziare.")

# Gestore per il nome della squadra
async def squadra_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    squadra = update.message.text
    logging.info(f"Squadra cercata: {squadra}")

    try:
        matches = get_team_matches(squadra)
        if matches == {"error": "API limit exceeded or invalid response"}:
            await update.message.reply_text(
                "⚠️ Il limite giornaliero delle richieste API è stato raggiunto o la risposta API non è valida. Non è possibile effettuare ulteriori ricerche oggi. Riprova domani!"
            )
            return

        logging.info(f"Partite trovate: {matches}")

        if matches:
            keyboard = [
                [InlineKeyboardButton(f"{match['teams']['home']['name']} vs {match['teams']['away']['name']} ({match['fixture']['date']})", callback_data=str(match['fixture']['id']))]
                for match in matches
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"Partite trovate per {squadra}:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Nessuna partita trovata per questa squadra. Riprova.")
    except Exception as e:
        logging.error(f"Errore durante il recupero delle partite: {e}")
        await update.message.reply_text("⚠️ Si è verificato un errore durante il recupero delle partite.")

# Gestore per la selezione della partita
async def match_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    match_id = query.data
    logging.info(f"Match ID selezionato: {match_id}")

    try:
        probability, details = calculate_probability(match_id)
        logging.info(f"Dettagli probabilità: {details}")

        if not details:
            await query.edit_message_text("⚠️ Errore nell'ottenere i dettagli della partita. Riprova più tardi.")
            return

        message = (
            f"📊 **Analisi della partita**:\n\n"
            f"🏠 **Squadra Casa**: {details['home_team']}\n"
            f"🏟️ **Squadra Ospite**: {details['away_team']}\n\n"
            f"⚽ **Media Gol Primo Tempo**:\n"
            f"   - Casa: {details['home_avg_goals']:.2f}\n"
            f"   - Ospite: {details['away_avg_goals']:.2f}\n\n"
            f"📈 **Percentuale Over 1.5 Primo Tempo**:\n"
            f"   - Casa: {details['home_over_1_5']:.2f}%\n"
            f"   - Ospite: {details['away_over_1_5']:.2f}%\n\n"
            f"🤝 **Scontri Diretti (H2H)**:\n"
            f"   - Media Gol Primo Tempo: {details['h2h_avg_goals']:.2f}\n"
            f"   - Percentuale Over 1.5 Primo Tempo: {details['h2h_over_1_5']:.2f}%\n\n"
            f"🔮 **Probabilità Over 1.5 Gol Primo Tempo**: {probability:.2f}%"
        )
        await query.edit_message_text(text=message, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Errore durante il calcolo della probabilità: {e}")
        await query.edit_message_text("⚠️ Si è verificato un errore durante il calcolo della probabilità. Riprova più tardi.")

# Gestore globale per gli errori
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Errore catturato: {context.error}")
    if update and isinstance(update, Update) and update.effective_user:
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="⚠️ Si è verificato un errore imprevisto. Il bot continua a funzionare."
        )

# Funzione principale
def main():
    logging.info("Avvio del bot...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Registra i gestori
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, squadra_handler))
    application.add_handler(CallbackQueryHandler(match_callback_handler))
    application.add_error_handler(error_handler)

    # Avvia il bot
    application.run_polling()


if __name__ == "__main__":
    main()
