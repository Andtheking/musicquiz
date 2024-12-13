from requirements import *
from utils.log import log

import asyncio
from music import Main
import random
from peewee import fn

from datetime import datetime

async def sendQuizJob(context: ContextTypes.DEFAULT_TYPE):

    if datetime.now().hour < 7:
        return

    for chat in Chat.select():
        chat: Chat
        
        if not chat.automatic_quizzes or chat.guessing:
            continue
        
        s = asyncio.Semaphore(3)
        asyncio.create_task(sendQuiz(context, chat, s))
    pass


async def sendQuiz(context: ContextTypes.DEFAULT_TYPE, chat: Chat, sem: asyncio.Semaphore):
    
    ok = False
    mex = None
    while not ok:
        wrong = []
        
        chat_user: Utente = (
            Utente
                .select()
                .join(ChatUserPoints)
                .where((Utente.lastfm != None) & (ChatUserPoints.chat == chat) & (Utente.id.not_in(wrong)))
                .order_by(fn.RANDOM())
                .limit(1)
                .get_or_none()
        )
        
        if chat_user is None:
            if mex is not None:
                await mex.delete()
            chat.guessing = False
            chat.save()
            return
        
        async with sem:        
            mex: Message = await context.bot.send_message(chat_id=chat.id, text="⏳")
            r = await Main(chat_user.lastfm)  # "Main" deve essere asincrona per questa chiamata
            
            if r is None:
                wrong.append(chat_user.id)
            else:
                ok = True
                
                try:
                    await mex.delete()
                except:
                    pass
                
                chat.guessing = True
                chat.save()
            
    track, file = r
    
    ok = False
    while not ok:
        try:
            async with sem: 
                await context.bot.send_audio(chat_id=chat.id, audio=open(file, 'rb'), title='Guess the song')
            ok = True
        except:
            log("Failed to send audio...", tipo='errore')
            pass

    chat.points = True
    chat.solution_title = '\n'.join(track[0])
    chat.solution_artist = '\n'.join(track[1])
    chat.guessing_from_who = chat_user.lastfm
    
    chat.job_id = context.job_queue.run_once(callback=time_limit, when=10*60, chat_id=chat.id, data=chat.id).job.id
    
    async with sem: 
        chat.save()
    
async def time_limit(context: ContextTypes.DEFAULT_TYPE):
    
    db_chat: Chat = Chat.get_by_id(context.job.data)
    
    canzone = db_chat.solution_title
    artista = db_chat.solution_artist
    profilo = db_chat.guessing_from_who
    
    db_chat.guessing = False
    db_chat.solution_artist = None
    db_chat.solution_title = None
    db_chat.guessing_from_who = None
    db_chat.points = False
    
    db_chat.save()
    
    await context.bot.send_message(
        chat_id=context.job.data,
        text="Tempo scaduto per indovinare la canzone! Era {canzone} di {artista} dal profilo di {profilo}.".format(
            canzone = canzone.split("\n")[0],
            artista = artista.split("\n")[0],
            profilo = profilo
        )
    )