from requirements import *

async def switchQuizMode (update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    db_chat: Chat = Chat.get_by_id(chat.id)
    
    
    db_chat.automatic_quizzes = not db_chat.automatic_quizzes
    db_chat.save()
    
    if db_chat.automatic_quizzes:
        await rispondi(message, "Abilitati i quiz automatici.")
    else:
        await rispondi(message, "Disabilitati i quiz automatici.")
        
    