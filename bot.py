import telebot
import requests
import os
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_KEY = os.getenv('LEUL_API_KEY')  
BASE_API_URL = 'https://verifyapi.leulzenebe.pro'

if not TELEGRAM_BOT_TOKEN or not API_KEY:
    raise ValueError("⚠️ Missing API keys! Please check your .env file.")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def format_response(response_data):
    """
    Formats the JSON response from the API into a readable Telegram message using HTML.
    """
    message = "🧾 <b>Verification Result:</b>\n\n"
    for key, value in response_data.items():
        if isinstance(value, dict):
            message += f"<b>{str(key).capitalize()}</b>:\n"
            for k, v in value.items():
                message += f"  - {str(k)}: <code>{str(v)}</code>\n"
        else:
            message += f"<b>{str(key).capitalize()}</b>: <code>{str(value)}</code>\n"
    return message

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Welcome to the Payment Verifier Bot!\n\n"
        "I can verify transactions for <b>Telebirr, CBE, Dashen, Abyssinia, CBEBirr, and M-Pesa</b>.\n\n"
        "👉 <b>Send me a Reference Number</b> (Text)\n"
        "   <i>(For CBE, send Reference + Last 8 digits of account. Ex: <code>FT12345 09945644</code>)</i>\n"
        "👉 <b>Send me a Receipt Screenshot</b> (Image)"
    )
    bot.reply_to(message, welcome_text, parse_mode='HTML')

# Handle Text Inputs (Universal Verification)
@bot.message_handler(content_types=['text'])
def handle_text(message):
    parts = message.text.strip().split()
    reference_number = parts[0]
    suffix = parts[1] if len(parts) > 1 else None

    if suffix:
        bot.reply_to(message, f"🔍 Checking reference: <code>{reference_number}</code> with suffix <code>{suffix}</code>...", parse_mode='HTML')
    else:
        bot.reply_to(message, f"🔍 Checking reference: <code>{reference_number}</code>...", parse_mode='HTML')
    
    url = f"{BASE_API_URL}/verify"
    headers = {
        'x-api-key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {"reference": reference_number}
    if suffix:
        payload["suffix"] = suffix
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            bot.reply_to(message, format_response(data), parse_mode='HTML')
        else:
            try:
                err_data = response.json()
                bot.reply_to(message, f"❌ <b>Verification Failed:</b>\n<code>{err_data.get('error', response.text)}</code>", parse_mode='HTML')
            except:
                bot.reply_to(message, f"❌ <b>API Error ({response.status_code}):</b>\n<code>{response.text}</code>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"⚠️ <b>Server connection error:</b> {str(e)}", parse_mode='HTML')

# Handle Image Inputs (Image Verification)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📷 Image received! Sending to Verifier API OCR...")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        url = f"{BASE_API_URL}/verify-image"
        headers = {
            'x-api-key': API_KEY
        }
        
        files = {
            'file': ('receipt.jpg', downloaded_file, 'image/jpeg') 
        }
        
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            bot.reply_to(message, format_response(data), parse_mode='HTML')
        else:
            try:
                err_data = response.json()
                bot.reply_to(message, f"❌ <b>Image Verification Failed:</b>\n<code>{err_data.get('error', response.text)}</code>", parse_mode='HTML')
            except:
                bot.reply_to(message, f"❌ <b>Image API Error ({response.status_code}):</b>\n<code>{response.text}</code>", parse_mode='HTML')
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ <b>Error processing image:</b> {str(e)}", parse_mode='HTML')

print("Bot is running and listening for messages...")
bot.infinity_polling()