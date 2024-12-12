from requirements import *

async def getPoints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    mex = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    
    
    db_chat = Chat.get_by_id(chat.id)
    db_user = Utente.get_by_id(user.id)

    points = ChatUserPoints.select().where((ChatUserPoints.chat == db_chat) & (ChatUserPoints.user == db_user)).first().points
    await rispondi(mex, f"{user.name} hai {points} punti in questa chat.")

async def getOtherPoints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mex = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    
    
    db_chat = Chat.get_by_id(chat.id)

    username = context.match.groupdict()['username']
    db_user = Utente.select().where(Utente.username == username).first()

    points = ChatUserPoints.select().where((ChatUserPoints.chat == db_chat) & (ChatUserPoints.user == db_user)).first()
    
    if points:
        points = points.points
    else:
        await rispondi(mex, f"Non ho trovato un utente con quell'username.")
        return
    await rispondi(mex, f"{user.name} hai {points} punti in questa chat.")
    
    
async def getClassifica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mex = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    
    db_chat = Chat.get_by_id(chat.id)
    points = ChatUserPoints.select().where((ChatUserPoints.chat == db_chat)).order_by(ChatUserPoints.points.desc())
    
    classifica = f"Classifica nella chat {chat.effective_name}\n\n"
    
    p: ChatUserPoints
    for i,p in enumerate(points):
        
        if i == 0:
            pos = '🥇'
        elif i == 1:
            pos = '🥈'
        elif i == 2:
            pos = '🥉'
        else:
            pos = f'{i+1})'
            
        classifica += f"{pos} {p.user.username} - {p.points}\n"
    
    
    await rispondi(mex, classifica)
    