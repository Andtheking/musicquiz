from peewee import *
from playhouse.migrate import SqliteMigrator, migrate

# Connettiamo al database SQLite
db = SqliteDatabase('secret/Database.db')

class BaseModel(Model):
    class Meta:
        database = db
        
class Utente(BaseModel):
    id = IntegerField(primary_key=True)
    username = TextField(null=True)
    admin = BooleanField(default=False)
    lastfm = TextField(null=True)
    
class Chat(BaseModel):
    id = IntegerField(primary_key=True)
    title = TextField(null=True)
    automatic_quizzes = BooleanField(null=False, default=True)
    
    job_id = IntegerField(null=True)
    guessing = BooleanField(null=False, default=True)
    points = BooleanField(default=False)
    guessing_from_who = TextField(null=True)
    solution_title = TextField(null=True)
    solution_artist = TextField(null=True)
    
class ChatUserPoints(BaseModel):
    user = ForeignKeyField(Utente)
    chat = ForeignKeyField(Chat)
    points = IntegerField(null=False, default=0)


# Funziona solo per aggiungere una colonnna o rinominarla
def add_column(tabella: str, colonna: str, tipo: Field):
    migrator = SqliteMigrator(db)
    # Esempio di migrazioni
    with db.atomic():
        # Aggiunta di una colonna
        migrate(
            migrator.add_column(tabella, colonna, tipo)
        )

def alter_column(tabella: str, colonna: str, tipo: Field):
    migrator = SqliteMigrator(db)
    # Esempio di migrazioni
    with db.atomic():
        # Aggiunta di una colonna
        migrate(
            migrator.alter_column_type(tabella, colonna, tipo)
        )
    

# Rimozione di una colonna non è supportata nativamente, ma puoi simulare:
# 1. Creare una nuova tabella senza la colonna.
# 2. Copiare i dati nella nuova tabella.
# 3. Rimuovere la vecchia tabella.
        
if __name__ == '__main__':
    alter_column('chat', 'job_id',TextField(null=True))