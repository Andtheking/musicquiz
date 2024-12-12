from requirements import *

TOKEN = load_configs()['token']  # TOKEN DEL BOT
CANALE_LOG = load_configs()['canale_log'] # Se vuoi mandare i log del bot in un canale telegram, comodo a parere mio.
persistence = PicklePersistence('bot.pkl')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE): # /start
    await update.message.reply_text(f'Hai avviato il bot, congrats')

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE): # /help
    await update.message.reply_text("""Una volta ogni 2 ore sarà mandata una canzone da un profilo a caso di quelli registrati al bot.
2 punti se si indovina una canzone di un profilo altrui, 1 punto se si indovina una propria canzone.
Il comando /startGuess rimarrà attivo, ma non darà punti.

Per aggiungere i vostri profili dai possibili random /setLastFm NomeUtente""")

# Segnala quando il bot crasha, con motivo del crash
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log(f'Update "{update}" caused error "{context.error}"',context.bot, "error")

def cancel(action: str): 
    async def thing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.effective_message.reply_text(f"Ok, azione \"{action}\" annullata")
        return ConversationHandler.END
    return thing

def message_handler_as_command(command, other=None, strict=True):
    return filters.Regex(re.compile(rf"^[!.\/]{command}(?P<botSignature>@{config.BOT_USERNAME})?{'( ' + other + ')?' if other is not None else ''}{'$' if strict else ''}",re.IGNORECASE))

from datetime import datetime, time

def main():
    # Avvia il bot
    application = Application.builder().token(TOKEN).persistence(persistence).build() # Se si vuole usare la PicklePersistance bisogna aggiungere dopo .token(TOKEN) anche .persistance(OGGETTO_PP)

    handlers = {
        "start": MessageHandler(message_handler_as_command('start'),middleware(start)),
        "help": MessageHandler(message_handler_as_command('help'),middleware(help)),
        "addAdmin": MessageHandler(message_handler_as_command('addAdmin','(?P<candidate>.+)?'), middleware(addAdmin)),
        "removeAdmin": MessageHandler(message_handler_as_command('removeAdmin','(?P<candidate>.+)?'), middleware(removeAdmin)),
        "startGuess": MessageHandler(message_handler_as_command('startGuess','(?P<username>.+)?'), middleware(startGuess_command)),
        "stopGuess": MessageHandler(message_handler_as_command('stopGuess'), middleware(stopGuess_command)),
        "setLastFmUser": MessageHandler(message_handler_as_command('setLastFm',"(?P<username>.+)?"), middleware(setLastFmUser)),
        "points": MessageHandler(message_handler_as_command('points'), middleware(getPoints)),
        "points2": MessageHandler(message_handler_as_command('points',"(?P<username>.+)?"), middleware(getOtherPoints)),
        "classifica": MessageHandler(message_handler_as_command('classifica'), middleware(getClassifica)),
    }
    
    for v in handlers.values():
        application.add_handler(v,0)
    
    # Se non cadi in nessun handler, vieni qui
    application.add_handler(MessageHandler(filters=filters.ALL, callback=middleware()),1)
    
    application.add_error_handler(error) # Definisce la funzione che gestisce gli errori
    
    jq = application.job_queue # Per eseguire funzioni asincrone con frequenza, ritardi o a pianificazione.
    

    if not load_configs()['test']:
        jq.run_repeating(
            callback=send_logs_channel,
            interval=60
        )

    jq.run_once(
        callback = initialize,
        when = 1
    )

    
    # jq.run_repeating(
    #     callback=sendQuizJob,
    #     interval=7200
    # )
    
    application.run_polling() # Avvia il polling: https://blog.neurotech.africa/content/images/2023/06/telegram-polling-vs-webhook-5-.png 
    
# Stabilisce che il codice sarà avviato solo quando il file è aperto direttamente, e non da un altro programma
# (Devi avviare il .py direttamente, rendendolo così il __main__)
if __name__ == '__main__':
    main()