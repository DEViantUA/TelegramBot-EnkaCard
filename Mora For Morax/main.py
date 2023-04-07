import json,asyncio, re,telebot
from telebot.async_telebot import AsyncTeleBot
from enkcard import encard
from enkcard.src.tools import translation
import io

bot = bot = AsyncTeleBot('TOKEN_KEY_BOT')

database = {}


async def send_msg(peer,text,art = '', keyb = ''):
    if art != '':
        a = await bot.send_photo(peer,art,text,reply_markup = keyb, parse_mode='Markdown',)
        return a.message_id
    else:
        a = await bot.send_message(peer, text, reply_markup = keyb, parse_mode='Markdown',)
        return a.message_id

async def edit_msg(peer,msg,texts = None,art = '', keyb = ''):
    if art != "":
        media = telebot.types.InputMediaPhoto(art, caption='')
        await bot.edit_message_media(chat_id=peer, message_id= msg, media=media, reply_markup=keyb)
    else:
        await bot.edit_message_text(chat_id=peer, message_id=msg, text = texts)


@bot.message_handler(commands=['help','start'])
async def start_help(message, res=False):
    chat_id = message.chat.id
    text = "✨Welcome! I'm Mora for Morax to create your Genshin Impact character cards.\n\nTo use the bot, use the command: `enkcard` it only supports 2 parameters UID and language.\n\nExample:\n`enkcard 123456789 en`\n\n⚠ If the buttons do not appear, then make sure that you have enabled the visibility of the character showcase in the game."
    await send_msg(chat_id,text,keyb = None)

@bot.callback_query_handler(func=lambda call: True)
async def callbak(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    mess_id = call.message.message_id
    calls = json.loads(call.data)
    ch = calls.get("ch")
    type_call = calls.get('type')
    if type_call == 'encard':
        async with encard.ENCard(lang=database[user_id].lang, characterName=ch) as enc:
            result = await enc.create_cards(database[user_id].uid)

        b = telebot.types.InlineKeyboardMarkup()
        button = []
        for character in database[user_id].charter:
            button.append(telebot.types.InlineKeyboardButton(character.name, callback_data=json.dumps({"type": "encard", "ch": character.name})))
            if len(button) == 4:
                b.row(*button)
                button = []
        if button:
            b.row(*button)
        with io.BytesIO() as cards:
            result.card[0].card.save(cards, "png")
            cards.seek(0)

            await edit_msg(chat_id, mess_id, art=cards, keyb=b)




# Получение сообщений от юзера
@bot.message_handler(content_types=["text"])
async def handle_text(message):
    uid = message.from_user.id
    chat_id = message.chat.id
    text_id = message.text.lower()


    if text_id.startswith("enkcard "):
        data = re.findall(r"enkcard \s*(.*?)\s*(?:\n| )\s*(.*?)\s*(?:\n| )\s*(.*?)$", text_id, re.DOTALL)
        if not data:
            await send_msg(chat_id, "❌ The command was entered incorrectly.")
            return

        data = data[0]
        lang = data[2] if data[2] in translation.supportLang else "en"
        try:
            async with encard.ENCard(lang=lang) as enc:
                result = await enc.create_profile(data[0])
                database[uid] = result

                text = f"ℹ {result.name}〔{result.uid}〕✦\n🤴Characters:〔{len(result.charter)}〕"
                buttons = [
                    telebot.types.InlineKeyboardButton(
                        character.name,
                        callback_data='{"type": "encard", "ch": "' + character.name + '"}'
                    ) for character in result.charter
                ]

                markup = telebot.types.InlineKeyboardMarkup()
                for index in range(0, len(buttons), 4):
                    markup.row(*buttons[index: index + 4])

                with io.BytesIO() as cards:
                    result.card.save(cards, "png")
                    cards.seek(0)
                    await send_msg(chat_id, text, art=cards, keyb=markup)

        except Exception as e:
            print(e)
            await send_msg(chat_id, "❌ Some error has occurred.")

    else:
        await send_msg(chat_id, "❌ You must enter the 9 digit uid of your game profile in Genshin Impact")

# Запускаем бота
while True:
    try:
        asyncio.run(bot.polling(none_stop=True, interval=0))
    except Exception as e:
        print(e)
