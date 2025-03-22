from requirements import *
import asyncio
from music import Main
from jobs.sendQuiz import time_limit
async def startGuess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    groups = context.match.groupdict()
    if not groups['username']:
        await rispondi(update.effective_message, "Il comando è `/startGuess <username_lastfm>`.", parse_mode=ParseMode.MARKDOWN)
        return
    
    chat_db: Chat = Chat.get_by_id(update.effective_chat.id)
    if chat_db.guessing:
        await rispondi(update.effective_message, "È già in corso un quiz")
        return
    
    chat_db.guessing = True
    chat_db.points = True

    chat_db.job_id = context.job_queue.run_once(callback=time_limit, when=10*60, chat_id=chat_db.id, data=chat_db.id).job.id
    chat_db.save()
    
    
    # Crea un task per eseguire la logica in modo asincrono e parallelo
    asyncio.create_task(startGuess_task(update, context))

async def startGuess_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    groups = context.match.groupdict()
    chat_db: Chat = Chat.get_by_id(update.effective_chat.id)

    mex: Message = await rispondi(update.effective_message, "⏳")
    
    # Scarica il file e ottieni le informazioni della traccia
    r = await Main(groups['username'])  # `Main` deve essere sincrona per questa chiamata
    if r is None:
        await rispondi(update.effective_message, "Non ho trovato un account last.fm con quel nome.")
        await mex.delete()
        chat_db.guessing = False
        chat_db.save()
        return

    track, file = r
    
    # Aggiorna lo stato del quiz nel database
    
    chat_db.solution_title = '\n'.join(track[0])
    chat_db.solution_artist = '\n'.join(track[1])
    chat_db.guessing_from_who = groups['username']
    chat_db.save()

    # Prova a inviare l'audio
    try:
        await update.effective_message.reply_audio(audio=open(file, 'rb'), title='Guess the song')
    except:
        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(file, 'rb'), title='Guess the song')

    await mex.delete()
    
    
async def stopGuess_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_db: Chat = Chat.get_by_id(update.effective_chat.id)
    
    if not chat_db.guessing:
        await rispondi(update.effective_message, "Non c'è bisogno di stoppare, non è in corso nulla")
        return
    
    try:
        await rispondi(update.effective_message, f"Ok, la canzone era \"{chat_db.solution_title.split('\n')[0]}\" di \"{chat_db.solution_artist.split('\n')[0]}\" dal profilo di \"{chat_db.guessing_from_who}\". Ora puoi usare /startGuess")
    except:
        pass
    
    
    chat_db.guessing = False
    chat_db.points = False
    
    chat_db.solution_artist = None
    chat_db.solution_title = None
    chat_db.guessing_from_who = None
    
    try:
        [k for k in context.job_queue.jobs() if k.id == chat_db.job_id][0].job.remove()
    except:
        pass
    chat_db.job_id = None
    
    chat_db.save()
    
    