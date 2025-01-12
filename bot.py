import logging
import re
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.constants import ParseMode
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Store user states and messages
user_states = {}
user_messages = {}

async def call_gemini_api(prompt, system_message):
    """Call Gemini API."""
    try:
        chat = model.start_chat(history=[])
        response = chat.send_message(
            f"{system_message}\n\n{prompt}"
        )
        
        return response.text
        
    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise

def get_main_keyboard():
    """Get the main keyboard with action buttons."""
    keyboard = [
        [
            InlineKeyboardButton("✨ প্রম্পট অপটিমাইজ করুন", callback_data='optimize_prompt'),
        ],
        [
            InlineKeyboardButton("🔄 টেক্সট স্টাইল পরিবর্তন", callback_data='convert_text'),
        ],
        [
            InlineKeyboardButton("📝 গিট কমিট মেসেজ তৈরি", callback_data='git_commit')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_style_keyboard():
    """Get the keyboard with text style options."""
    keyboard = [
        [
            InlineKeyboardButton("📋 ফরমাল স্টাইল", callback_data='style_formal'),
            InlineKeyboardButton("😊 ক্যাজুয়াল স্টাইল", callback_data='style_casual')
        ],
        [
            InlineKeyboardButton("👔 প্রফেশনাল স্টাইল", callback_data='style_professional'),
            InlineKeyboardButton("🤝 বন্ধুসুলভ স্টাইল", callback_data='style_friendly')
        ],
        [
            InlineKeyboardButton("🔙 পিছনে যান", callback_data='back_to_main')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        '🌟 *স্বাগতম\\!*\n\n'
        'আমি একটি AI\\-পাওয়ার্ড বট। আপনার টেক্সট অপটিমাইজ করতে পারি।\n\n'
        '📋 *বটের ফিচারসমূহ:*\n\n'
        '1️⃣ *প্রম্পট অপটিমাইজেশন* ✨\n'
        '• Gemini এর জন্য প্রম্পট অপটিমাইজ করে\n'
        '• ভালো রেসপন্স পাওয়ার জন্য প্রম্পট ইম্প্রুভ করে\n'
        '• AI এর জন্য পারফেক্ট প্রম্পট তৈরি করে\n\n'
        '2️⃣ *টেক্সট স্টাইল পরিবর্তন* 🔄\n'
        '• ফরমাল স্টাইল \\- আনুষ্ঠানিক ও শ্রদ্ধাশীল ভাষা\n'
        '• ক্যাজুয়াল স্টাইল \\- সহজ ও বন্ধুসুলভ ভাষা\n'
        '• প্রফেশনাল স্টাইল \\- ব্যবসায়িক ও পেশাদার ভাষা\n'
        '• বন্ধুসুলভ স্টাইল \\- আন্তরিক ও মজার ভাষা\n\n'
        '3️⃣ *গিট কমিট মেসেজ* 📝\n'
        '• গিট কমিট মেসেজ অপটিমাইজ করে\n'
        '• বেস্ট প্র্যাকটিস অনুযায়ী মেসেজ তৈরি করে\n'
        '• কমিট মেসেজের ফরম্যাট ঠিক করে\n\n'
        '📱 *ব্যবহার পদ্ধতি:*\n'
        '1\\. যেকোনো টেক্সট লিখুন\n'
        '2\\. তারপর আপনার প্রয়োজন অনুযায়ী বাটন বেছে নিন\n'
        '3\\. AI আপনার টেক্সট অপটিমাইজ করে দিবে\n\n'
        '🤔 শুরু করতে যেকোনো টেক্সট লিখুন\\!',
        parse_mode=ParseMode.MARKDOWN_V2
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button presses."""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'back_to_main':
        if query.from_user.id in user_messages:
            text = user_messages[query.from_user.id]
            await query.message.edit_text(
                f"আপনার টেক্সট: \n\n{text}\n\n👇 কী করতে চান বেছে নিন:",
                reply_markup=get_main_keyboard()
            )
        return
    
    if query.data == 'convert_text':
        if query.from_user.id in user_messages:
            text = user_messages[query.from_user.id]
            await query.message.edit_text(
                f"আপনার টেক্সট: \n\n{text}\n\n👇 কোন স্টাইলে রূপান্তর করতে চান?",
                reply_markup=get_style_keyboard()
            )
        return
    
    elif query.data.startswith('style_'):
        style = query.data.replace('style_', '')
        if query.from_user.id in user_messages:
            text = user_messages[query.from_user.id]
            await convert_text_style(query.message, text, style)
    
    elif query.data == 'optimize_prompt':
        if query.from_user.id in user_messages:
            text = user_messages[query.from_user.id]
            await optimize_prompt_text(query.message, text)
    
    elif query.data == 'git_commit':
        if query.from_user.id in user_messages:
            text = user_messages[query.from_user.id]
            await optimize_commit_text(query.message, text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages."""
    text = update.message.text
    user_id = update.message.from_user.id
    
    # Store the message
    user_messages[user_id] = text
    
    # Show options
    await update.message.reply_text(
        f"আপনার টেক্সট: \n\n{text}\n\n👇 কী করতে চান বেছে নিন:",
        reply_markup=get_main_keyboard()
    )

def escape_markdown(text):
    """Escape Markdown special characters."""
    if text is None:
        return ""
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', str(text))

async def optimize_prompt_text(message, text):
    """Optimize prompt text."""
    try:
        system_message = """You are a helpful assistant that optimizes prompts for AI models like ChatGPT. 
        Your task is to improve the given prompt to get better responses from AI.
        Always respond in Bengali language only.
        Make the prompt clear, specific, and well-structured.
        Add necessary context and requirements.
        Break down complex requests into steps if needed."""
        
        optimized_text = await call_gemini_api(
            f"""Please optimize this prompt to get better results from AI models:

Original Prompt: {text}

Please:
1. Make it more specific and clear
2. Add necessary context
3. Include any important requirements
4. Break down complex parts
5. Improve the structure
6. Keep the response in Bengali language only

Optimized version:""",
            system_message
        )
        
        keyboard = [[InlineKeyboardButton("🔙 পিছনে যান", callback_data='back_to_main')]]
        await message.edit_text(
            f"✨ *অপটিমাইজড প্রম্পট:*\n\n{escape_markdown(optimized_text)}\n\n"
            "*টিপস:*\n"
            "• স্পষ্ট এবং নির্দিষ্ট প্রম্পট লিখুন\n"
            "• প্রয়োজনীয় কনটেক্সট যোগ করুন\n"
            "• জটিল অংশগুলি ভেঙে লিখুন",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Error in optimize_prompt_text: {str(e)}")
        await message.edit_text(
            "দুঃখিত, API কল করার সময় একটি ত্রুটি হয়েছে। দয়া করে আবার চেষ্টা করুন।",
            reply_markup=get_main_keyboard()
        )

async def convert_text_style(message, text, style):
    """Convert text to a specific style."""
    try:
        style_prompts = {
            'formal': """Convert this text to a formal and professional tone.
                       Make it appropriate for official communication.
                       Use respectful and sophisticated language.
                       Keep the response in Bengali language only.""",
            
            'casual': """Make this text more casual and friendly.
                      Use everyday conversational language.
                      Make it sound natural and relaxed.
                      Keep the response in Bengali language only.""",
            
            'professional': """Transform this text into professional business language.
                           Make it clear, concise and impactful.
                           Use industry-standard terminology.
                           Keep the response in Bengali language only.""",
            
            'friendly': """Convert this text to a warm and friendly tone.
                        Make it engaging and approachable.
                        Use positive and encouraging language.
                        Keep the response in Bengali language only."""
        }
        
        if style not in style_prompts:
            await message.edit_text(
                "অবৈধ স্টাইল। অনুগ্রহ করে এই স্টাইলগুলির মধ্যে একটি বেছে নিন:\n"
                "• formal - আনুষ্ঠানিক\n"
                "• casual - অনানুষ্ঠানিক\n" 
                "• professional - পেশাদার\n"
                "• friendly - বন্ধুসুলভ",
                reply_markup=get_main_keyboard()
            )
            return
            
        system_message = """You are a helpful assistant that converts text to different styles while maintaining the original meaning.
        Always respond in Bengali language only.
        Keep the core message intact while adapting the tone and language."""
        
        converted_text = await call_gemini_api(
            f"""Please convert this text to the specified style:

Original Text: {text}

Style Instructions: {style_prompts[style]}

Converted version:""",
            system_message
        )
        
        keyboard = [[InlineKeyboardButton("🔙 পিছনে যান", callback_data='back_to_main')]]
        await message.edit_text(
            f"✨ *কনভার্টেড টেক্সট* \\({style}\\)*:*\n\n{escape_markdown(converted_text)}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Error in convert_text_style: {str(e)}")
        await message.edit_text(
            "দুঃখিত, API কল করার সময় একটি ত্রুটি হয়েছে। দয়া করে আবার চেষ্টা করুন।",
            reply_markup=get_main_keyboard()
        )

async def optimize_commit_text(message, text):
    """Optimize git commit message."""
    try:
        system_message = """You are a helpful assistant that optimizes git commit messages following best practices.
        Always respond in Bengali language only.
        Follow these rules:
        1. First line should be a short summary (max 50 characters)
        2. Use imperative mood (add, not added)
        3. Capitalize the first letter
        4. Don't end with a period
        5. Add detailed description in new lines if needed
        6. Keep it clear and descriptive"""
        
        optimized_message = await call_gemini_api(
            f"""Please optimize this git commit message following best practices:

Original Message: {text}

Please:
1. Create a short summary line (max 50 chars)
2. Use imperative mood (add, not added)
3. Add detailed description if needed
4. Follow the git commit message convention
5. Keep the response in Bengali language only

Optimized version:""",
            system_message
        )
        
        keyboard = [[InlineKeyboardButton("🔙 পিছনে যান", callback_data='back_to_main')]]
        await message.edit_text(
            f"📝 *অপটিমাইজড কমিট মেসেজ:*\n\n{escape_markdown(optimized_message)}\n\n"
            "*টিপস:*\n"
            "• প্রথম লাইনে সংক্ষিপ্ত সারাংশ \\(50 অক্ষরের মধ্যে\\)\n"
            "• বর্তমান কাল ব্যবহার করুন \\(add না added\\)\n"
            "• প্রথম অক্ষর বড় হাতের হবে\n"
            "• শেষে ফুলস্টপ দিবেন না\n"
            "• প্রয়োজনে বিস্তারিত বর্ণনা নতুন লাইনে দিন",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Error in optimize_commit_text: {str(e)}")
        await message.edit_text(
            "দুঃখিত, API কল করার সময় একটি ত্রুটি হয়েছে। দয়া করে আবার চেষ্টা করুন।",
            reply_markup=get_main_keyboard()
        )

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start the Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main() 