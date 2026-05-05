# filepath: app.py
from flask import Flask, render_template, request, jsonify
import nltk
from nltk.chat.util import Chat

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

app = Flask(__name__)

# Store user's session state, including preferred religion
user_sessions = {}

# Greetings by religion
religion_greetings = {
    'islam': ['☪️ Assalamu Alaikum! Welcome to Deen Ki Duniya!', '☪️ As-salamu alaykum! Peace be upon you!'],
    'christianity': ['✝️ Good day! Welcome to Deen Ki Duniya!', '✝️ God bless you! Welcome!'],
    'hinduism': ['🕉️ Namaste! Welcome to Deen Ki Duniya!', '🕉️ Sadhu! Welcome to the world of faith!'],
    'buddhism': ['🪷 Sadhu! Welcome to Deen Ki Duniya!', '🪷 Blessings of Buddha! Welcome!'],
    'judaism': ['✡️ Shalom! Welcome to Deen Ki Duniya!', '✡️ Peace be with you! Welcome!'],
    'sikhism': ['🪖 Waheguru Ji Ka Khalsa! Welcome to Deen Ki Duniya!', '🪖 Sat Sri Akal! Welcome!']
}

# Religion selection prompt
religion_prompt = "Which religion are you interested in learning about? (Islam, Christianity, Hinduism, Buddhism, Judaism, Sikhism)"

# Religious chatbot pairs (40+ pairs) with regex patterns
pairs = [
    # Greetings
    (r'hi|hello|hey|salaam|namaste', ['Assalamu Alaikum! Welcome to Deen Ki Duniya. How can I help you today?', 'Namaste! Welcome to the world of religion. What would you like to know?']),
    (r'how are you|kaisa hai|kaise hain', ['I am always ready to help you learn about religions. Alhumdulillah!', 'I am fine, thank you! Ready to answer your questions about faith.']),
    
    # About Religion
    (r'what is religion|religion kya hai|dharm kya hai', ['Religion is a system of beliefs, practices, and values that relate to the sacred or divine. It guides millions of lives worldwide.', 'Religion is the belief in a supreme power and following its teachings for a meaningful life.']),
    (r'tell me about religions|duniya ke dharm|religion ke baare mein', 'There are many major religions in the world: Islam, Christianity, Hinduism, Buddhism, Judaism, Sikhism, and more. Each has its own beliefs and practices.'),
    
    # Islam
    (r'islam|muslim|muslims', ['Islam is the second largest religion. Muslims believe in one God (Allah) and follow the Quran. The five pillars are: Shahada, Salat, Zakat, Sawm, and Hajj.']),
    (r'quran|kuran|holy book', ['The Quran is the holy book of Muslims, revealed to Prophet Muhammad (PBUH). It contains guidance for all aspects of life.']),
    (r'prayer|namaz|salat', ['Salat (prayer) is performed 5 times a day. It is one of the five pillars of Islam and a direct connection with Allah.']),
    (r'ramadan|fasting|roza', ['Ramadan is the holy month of fasting. Muslims fast from dawn to sunset, abstaining from food, drink, and bad thoughts.']),
    
    # Christianity
    (r'christianity|christians|isa', ['Christianity is the largest religion. Christians believe in Jesus Christ as the Son of God and follow the Bible.']),
    (r'bible|injil|holy bible', ['The Bible is the holy book of Christians, consisting of the Old and New Testaments. It contains teachings of God and Jesus Christ.']),
    (r'jesus|isa|messiah', ['Jesus Christ is the central figure of Christianity. He is believed to be the Son of God and the Messiah.']),
    (r'church|girja|mandir', ['Church is the place of worship for Christians where they gather for prayer and fellowship.']),
    
    # Hinduism
    (r'hinduism|hindu|hindu dharm', ['Hinduism is one of the oldest religions. Hindus believe in many deities and follow the Vedas and other scriptures.']),
    (r'vedas|shastra|holy books', ['The Vedas are the oldest Hindu scriptures. They include Rig, Yajur, Sama, and Atharva Vedas.']),
    (r'god|deity|devta', ['Hinduism has many gods: Brahma (creator), Vishnu (preserver), Shiva (destroyer), Lakshmi, Saraswati, and more.']),
    (r'caste|jati|varna', ['The caste system is a traditional Hindu social division into four varnas: Brahmin, Kshatriya, Vaishya, and Shudra.']),
    
    # Buddhism
    (r'buddhism|buddha|buddhist', ['Buddhism is based on the teachings of Siddhartha Gautama (Buddha). It focuses on ending suffering through the Eightfold Path.']),
    (r'nirvana|moksha|nibban', ['Nirvana is the ultimate goal in Buddhism - liberation from the cycle of birth and death (samsara).']),
    (r'meditation|dhyana|meditate', ['Meditation is important in Buddhism. It helps calm the mind and achieve spiritual growth.']),
    
    # Judaism
    (r'judaism|jews|yahudi', ['Judaism is the oldest monotheistic religion. Jews believe in one God and follow the Torah.']),
    (r'torah|tanakh|holy book', ['The Torah is the holy book of Jews containing the five books of Moses. It is the foundation of Jewish law.']),
    (r'synagogue|shul|ibadaat', ['Synagogue is the Jewish place of worship and community center.']),
    
    # Sikhism
    (r'sikhism|sikh|guru', ['Sikhism was founded by Guru Nanak Dev. Sikhs believe in one God and follow the teachings of the ten Gurus.']),
    (r'guru granth sahib|ad granul|holy book', ['Guru Granth Sahib is the holy book of Sikhs, containing hymns of the Gurus and Hindu and Muslim saints.']),
    (r'gurdwara|harmandir|sikh temple', ['Gurdwara is the Sikh place of worship. The Golden Temple in Amritsar is the most sacred.']),
    
    # General Religious Concepts
    (r'god|allah|parmeshwar|parmatma', ['Most religions believe in a supreme being or power - whether called God, Allah, Brahman, or by other names.']),
    (r'prayer|dua|worship|ibadat', ['Prayer is a way to connect with the divine. Every religion has its own form of prayer and worship.']),
    (r'faith|imaan|belief', ['Faith is the foundation of religion. It gives meaning and purpose to life.']),
    (r'holy|paak|pavitra|sacred', ['Holiness is a key concept in all religions - sacred places, texts, and times set apart for God.']),
    
    # Religious Practices
    (r'worship|ibadat|puja|puja', ['Worship practices vary: Muslims pray 5 times daily, Hindus do puja, Christians attend church, Buddhists meditate.']),
    (r'fasting|vrat|upvas|roza', ['Fasting is practiced in many religions: Ramadan (Islam), Lent (Christianity), Ekadashi (Hinduism), etc.']),
    (r'charity|zakat|sadaqah|daan', ['Charity is important in all religions. Islam has Zakat, Hinduism has Daan, Christianity has tithes.']),
    (r'pilgrimage|hajj|yatra|ziarat', ['Pilgrimage is important: Hajj (Mecca), Jerusalem (Judaism/Christianity/Islam), Varanasi (Hinduism), etc.']),
    
    # Religious Festivals
    (r'festival|utsav|eid|christmas|diwali', ['Religious festivals: Eid (Islam), Christmas (Christianity), Diwali (Hinduism), Buddha Purnima (Buddhism), etc.']),
    (r'eid|id|celebration', ['Eid is celebrated by Muslims: Eid-ul-Fitr after Ramadan, Eid-ul-Adha during Hajj.']),
    (r'diwali|deepavali|festival of lights', ['Diwali is the Hindu festival of lights, celebrating the victory of light over darkness.']),
    (r'christmas|yad|jesus birthday', ['Christmas celebrates the birth of Jesus Christ with decorations, gifts, and church services.']),
    
    # Interfaith
    (r'all religions|sab dharm|ekta', ['All religions teach love, peace, and compassion. Despite differences, they share common values.']),
    (r'peace|aman|shanti|amity', ['Peace is central to all religions. "Peace be upon you" (As-salamu Alaikum) is a universal greeting.']),
    (r'love|compassion|karuna|rehm', ['Love and compassion are taught in every religion. Help others and be kind.']),
    
    # Questions about the bot
    (r'who are you|kon ho tum|kaun ho', ['I am a chatbot about Deen Ki Duniya (World of Religion). I can answer your questions about different religions.']),
    (r'what can you tell me|ka info de sakte ho', ['I can tell you about Islam, Christianity, Hinduism, Buddhism, Judaism, Sikhism, and other religions.']),
    
    # Farewell
    (r'bye|exit|goodbye|alvida|shukriya', ['Thank you for chatting! May God bless you. Goodbye!', 'It was nice talking to you. Stay blessed! Goodbye!']),
]

# Create chatbot
chatbot = Chat(pairs, reflections={})

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get', methods=['GET', 'POST'])
def get_response():
    user_message = request.form.get('message') or request.args.get('message', '')
    session_id = request.remote_addr  # Use IP as simple session identifier
    
    if user_message.lower() in ['exit', 'bye', 'alvida', 'goodbye']:
        return jsonify({'response': 'Thank you for chatting about Deen Ki Duniya! May peace be upon you. Goodbye!', 'exit': True})
    
    # Check if user needs to select religion
    if session_id not in user_sessions:
        user_message_lower = user_message.lower()
        
        # Check for religion selection
        if any(word in user_message_lower for word in ['islam', 'muslim', 'quran']):
            user_sessions[session_id] = {'religion': 'islam'}
            import random
            greeting = random.choice(religion_greetings['islam'])
            return jsonify({'response': f"{greeting}\n\nGreat! I'll share information about Islam. Ask me anything!", 'exit': False})
        elif any(word in user_message_lower for word in ['christianity', 'christian', 'jesus', 'bible']):
            user_sessions[session_id] = {'religion': 'christianity'}
            import random
            greeting = random.choice(religion_greetings['christianity'])
            return jsonify({'response': f"{greeting}\n\nGreat! I'll share information about Christianity. Ask me anything!", 'exit': False})
        elif any(word in user_message_lower for word in ['hinduism', 'hindu', 'hindu dharm']):
            user_sessions[session_id] = {'religion': 'hinduism'}
            import random
            greeting = random.choice(religion_greetings['hinduism'])
            return jsonify({'response': f"{greeting}\n\nGreat! I'll share information about Hinduism. Ask me anything!", 'exit': False})
        elif any(word in user_message_lower for word in ['buddhism', 'buddha', 'buddhist']):
            user_sessions[session_id] = {'religion': 'buddhism'}
            import random
            greeting = random.choice(religion_greetings['buddhism'])
            return jsonify({'response': f"{greeting}\n\nGreat! I'll share information about Buddhism. Ask me anything!", 'exit': False})
        elif any(word in user_message_lower for word in ['judaism', 'jews', 'jewish']):
            user_sessions[session_id] = {'religion': 'judaism'}
            import random
            greeting = random.choice(religion_greetings['judaism'])
            return jsonify({'response': f"{greeting}\n\nGreat! I'll share information about Judaism. Ask me anything!", 'exit': False})
        elif any(word in user_message_lower for word in ['sikhism', 'sikh', 'guru']):
            user_sessions[session_id] = {'religion': 'sikhism'}
            import random
            greeting = random.choice(religion_greetings['sikhism'])
            return jsonify({'response': f"{greeting}\n\nGreat! I'll share information about Sikhism. Ask me anything!", 'exit': False})
        else:
            # First message - ask about religion interest
            return jsonify({'response': religion_prompt, 'exit': False})
    
    # User has selected religion - answer questions directly
    current_religion = user_sessions.get(session_id, {}).get('religion')
    
    # Get response from chatbot
    bot_response = chatbot.respond(user_message)
    
    if not bot_response:
        bot_response = "I'm sorry, I didn't understand. Please ask about any religion - Islam, Christianity, Hinduism, Buddhism, Judaism, Sikhism, or religious concepts like prayer, fasting, festivals, etc."
    
    return jsonify({'response': bot_response, 'exit': False})

if __name__ == '__main__':
    app.run(debug=True)