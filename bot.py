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

# We take the first manager ID from your .env file
MANAGER_ID = os.getenv('MANAGER_TG_IDS') 

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def format_response(response_data):
    """Formats JSON response to readable HTML."""
    message = ""
    for key, value in response_data.items():
        if isinstance(value, dict):
            message += f"<b>{str(key).capitalize()}</b>:\n"
            for k, v in value.items():
                message += f"  - {str(k)}: <code>{str(v)}</code>\n"
        else:
            message += f"<b>{str(key).capitalize()}</b>: <code>{str(value)}</code>\n"
    return message

def notify_manager(verification_data, merchant_chat_id, reference):
    """Sends the successful transaction to the Manager."""
    if not MANAGER_ID:
        return # Skip if manager ID is not set
        
    manager_msg = (
        "🔔 <b>NEW PAYMENT PENDING APPROVAL</b> 🔔\n\n"
        f"<b>Merchant ID:</b> <code>{merchant_chat_id}</code>\n"
        f"<b>Reference:</b> <code>{reference}</code>\n\n"
        "<b>--- API Details ---</b>\n"
        f"{format_response(verification_data)}"
    )
    
    # Send to Manager
    try:
        bot.send_message(MANAGER_ID, manager_msg, parse_mode='HTML')
        # Here we will eventually add the Inline Buttons [Approve] [Decline]
    except Exception as e:
        print(f"Failed to send to manager: {e}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Welcome to the Payment Verifier Bot!\n\n"
        "👉 <b>Send me a Reference Number</b>\n"
        "👉 <b>Send me a Receipt Screenshot</b>"
    )
    bot.reply_to(message, welcome_text, parse_mode='HTML')

# --- STEP 2: Handle the Suffix provided by the user ---
def process_cbe_suffix(message, reference_number):
    suffix = message.text.strip()
    bot.reply_to(message, f"🔍 Verifying Reference <code>{reference_number}</code> with suffix <code>{suffix}</code>...", parse_mode='HTML')
    
    url = f"{BASE_API_URL}/verify"
    headers = {'x-api-key': API_KEY, 'Content-Type': 'application/json'}
    payload = {"reference": reference_number, "suffix": suffix}
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Send to Merchant
            merchant_msg = f"🧾 <b>Final Verification Result:</b>\n\n{format_response(data)}\n\n⏳ <i>Sent to Manager for approval...</i>"
            bot.reply_to(message, merchant_msg, parse_mode='HTML')
            
            # Send to Manager
            notify_manager(data, message.chat.id, reference_number)
            
        else:
            bot.reply_to(message, f"❌ <b>Verification Failed:</b>\n<code>{response.text}</code>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"⚠️ <b>Error:</b> {str(e)}", parse_mode='HTML')

# --- STEP 1: Handle Images ---
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "📷 Image received! Running AI OCR...")
    
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        url = f"{BASE_API_URL}/verify-image"
        headers = {'x-api-key': API_KEY}
        files = {'file': ('receipt.jpg', downloaded_file, 'image/jpeg')}
        
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it needs a suffix (Like your CBE receipt did)
            if data.get("accountsuffix") == "required_from_user":
                ref = data.get("reference")
                
                # Ask the user for the suffix
                msg = bot.reply_to(message, f"⚠️ <b>CBE Receipt Detected!</b>\nOCR found reference: <code>{ref}</code>\n\nPlease reply with the <b>last 8 digits</b> of the receiver's account to complete verification:", parse_mode='HTML')
                
                # Tell the bot to wait for the user's next message and send it to process_cbe_suffix
                bot.register_next_step_handler(msg, process_cbe_suffix, ref)
            
            # If it's fully successful already (Like Telebirr)
            elif data.get("success") == True or data.get("status") == "success":
                merchant_msg = f"🧾 <b>Verification Result:</b>\n\n{format_response(data)}\n\n⏳ <i>Sent to Manager for approval...</i>"
                bot.reply_to(message, merchant_msg, parse_mode='HTML')
                
                notify_manager(data, message.chat.id, data.get("reference", "Unknown"))
                
            else:
                bot.reply_to(message, f"🧾 <b>Partial Result:</b>\n\n{format_response(data)}", parse_mode='HTML')

        else:
            bot.reply_to(message, f"❌ <b>Image API Error:</b>\n<code>{response.text}</code>", parse_mode='HTML')
            
    except Exception as e:
        bot.reply_to(message, f"⚠️ <b>Error processing image:</b> {str(e)}", parse_mode='HTML')

# --- Handle pure Text Reference (Fallback) ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    parts = message.text.strip().split()
    reference_number = parts[0]
    suffix = parts[1] if len(parts) > 1 else None

    bot.reply_to(message, f"🔍 Checking reference...", parse_mode='HTML')
    url = f"{BASE_API_URL}/verify"
    headers = {'x-api-key': API_KEY, 'Content-Type': 'application/json'}
    payload = {"reference": reference_number}
    if suffix: payload["suffix"] = suffix
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            bot.reply_to(message, format_response(data), parse_mode='HTML')
            notify_manager(data, message.chat.id, reference_number)
        else:
            bot.reply_to(message, f"❌ <b>Verification Failed:</b>\n<code>{response.text}</code>", parse_mode='HTML')
    except Exception as e:
        bot.reply_to(message, f"⚠️ <b>Error:</b> {str(e)}", parse_mode='HTML')

print("Bot is running...")
bot.infinity_polling()