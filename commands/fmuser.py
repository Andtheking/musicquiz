from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import *
from models.models import Utente
from utils.answerMessage import rispondi

async def setLastFmUser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    groups = context.match.groupdict()
    if not groups['username']:
        await rispondi(update.effective_message, "Il comando è `/setLastFm <username_lastfm>`.", parse_mode=ParseMode.MARKDOWN)
        return
    
    username = groups['username']
    dbU: Utente = Utente.get_by_id(update.effective_user.id)
    dbU.lastfm = username
    dbU.save()
    await rispondi(update.effective_message, f"Hai impostato correttamente \"{username}\" come profilo LastFM (Se hai sbagliato profilo, il bot ignorerà il tuo profilo nell'inoltro dei quiz)")
    
    pass