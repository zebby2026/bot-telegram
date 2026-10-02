import sqlite3
from datetime import datetime
from flask import Flask
from threading import Thread
import telebot

# Sostituisci con il TOKEN ottenuto da BotFather
TOKEN = '8969737938:AAGbi3iIYO-XmHDY86_ZBuqkUvWvi-ROEOY'
bot = telebot.TeleBot(TOKEN)

# Web Server per mantenere sveglio Render
app = Flask('')

@app.route('/')
def home():
    return "Bot contatore attivo!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Inizializza il database SQLite
def init_db():
    conn = sqlite3.connect('chat_stats.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS joins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Traccia i nuovi ingressi nel canale
@bot.chat_member_handler()
def track_joins(message):
    new_status = message.new_chat_member.status
    old_status = message.old_chat_member.status
    
    # Registra solo quando un utente entra effettivamente
    if old_status in ['left', 'kicked'] and new_status == 'member':
        today = datetime.now().strftime('%Y-%m')
        conn = sqlite3.connect('chat_stats.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO joins (user_id, date) VALUES (?, ?)', 
                       (message.new_chat_member.user.id, today))
        conn.commit()
        conn.close()

# Comando /stats in chat privata col bot
@bot.message_handler(commands=['stats'])
def show_stats(message):
    current_month = datetime.now().strftime('%Y-%m')
    conn = sqlite3.connect('chat_stats.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM joins WHERE date = ?', (current_month,))
    count = cursor.fetchone()[0]
    conn.close()
    
    bot.reply_to(message, f"📊 Ingressi registrati questo mese ({current_month}): *{count}*", parse_mode="Markdown")

if __name__ == '__main__':
    init_db()
    keep_alive()
    bot.infinity_polling(allowed_updates=["chat_member", "message"])
