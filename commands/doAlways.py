from requirements import *

from music import similar, format_title
from fuzzywuzzy import fuzz



# Questa funzione sarà eseguita prima di tutte le altre e per ogni messaggio che non è un comando
# TODO Spezzettae in diverse funzioni, è troppo lunga
def middleware(next = None):
    async def doAlways(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != ChatType.PRIVATE and load_configs()['test']:
            if not update.effective_message.chat_id in load_configs()['enabled_groups']:
                await update.effective_message.chat.leave()
                return
        user = update.effective_user
        message = update.effective_message
        chat = message.chat

       
        if user is not None:
            db_user: Utente = Utente.select().where(Utente.id == user.id).first()
            if db_user is None:
                db_user = Utente.create(id = user.id, username = user.name)
                log(f"Inserito nel DB il seguente utente: {user.name} ({user.id})", True)
            
            if db_user.username != user.name:
                old_name = db_user.username
                db_user.username = user.name
                db_user.save()
                log(f"L'utente {old_name} ha cambiato nome: {user.name} ({user.id})", True)
        
        db_chat: Chat = Chat.select().where(Chat.id == chat.id).first()
        if db_chat is None:
            db_chat = Chat.create(id = chat.id, title = chat.effective_name)
            log(f"Inserita nel DB la seguente chat: {chat.effective_name} ({chat.id})", True)
        
        if db_chat.title != chat.effective_name:
            old_title = db_chat.title
            db_chat.title = chat.effective_name
            db_chat.save()
            log(f"La chat {old_title} ha cambiato titolo: {chat.effective_name} ({chat.id})", True)
        
        if user is not None:
            cup: ChatUserPoints = (
                ChatUserPoints
                .select()
                .where((ChatUserPoints.user == db_user) & (ChatUserPoints.chat == db_chat))
                .first()
            )
            
            if cup is None:
                db_cup = ChatUserPoints.create(user = db_user, chat = db_chat)
                log(f"Creato un record per l'utente: {user.name} ({user.id}) nella chat {chat.effective_name} ({chat.id})", True)
        
        if db_chat.guessing and db_chat.solution_title:
            guess = format_title(update.effective_message.text)

            
            for i,j in zip(db_chat.solution_title.split("\n"),db_chat.solution_artist.split("\n")):
                correct_title, correct_artist = format_title(i, j)
                if correct_title and correct_artist and guess and (fuzz.ratio(correct_title.lower(), guess.lower()) >= 80):
                    if cup and db_chat.points:
                        other = db_user.lastfm != db_chat.guessing_from_who
                        punti_guadagnati = (2 if other else 1)
                        cup.points += punti_guadagnati
                        points_string = f"Hai ottenuto {punti_guadagnati} punt" + ("i perché il profilo non era tuo" if other else "o perché il profilo era tuo") + "."
                        cup.save()
                    else:
                        points_string = ""
                        
                    await rispondi(
                        update.effective_message, 
                        f"{user.name} hai indovinato il titolo della canzone! È \"{correct_title}\" di \"{correct_artist}\" presa dal profilo di \"{db_chat.guessing_from_who}\"." + points_string
                    )
                        
                    
                    db_chat.guessing = False
                    db_chat.points = False
                    
                    db_chat.solution_artist = None
                    db_chat.solution_title = None
                    db_chat.guessing_from_who = None
                    
                    try:
                        [k for k in context.job_queue.jobs() if k.id == db_chat.job_id][0].job.remove()
                    except:
                        pass
                    db_chat.job_id = None
                    
                    db_chat.save()
                    
                        

                    break
        
        if next != None:
            await next(update, context)
            
    return doAlways