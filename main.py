import asyncio
import base64
from aiogram import Bot, Dispatcher, types, F
import logging
from aiogram.filters import Command, CommandStart
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile

from gradio_client import Client
import requests
import utils as ut
import sync_utils as ut_s
import os
import re
import aiohttp
from ollama import AsyncClient
from concurrent.futures import ThreadPoolExecutor


bot = Bot(token="7065978461:AAERdf98TwjOO6RuilIlH4l0gUCy6jUAExI")
dp = Dispatcher()

# Создаем пул потоков
executor = ThreadPoolExecutor()

# Команды для пользователей
# user_commands = [
#     types.BotCommand(),
#     types.BotCommand(),
# ]

# async def set_commands(dp: Dispatcher):
#     await bot.set_my_commands(user_commands, scope=types.bot_command_scope_default.BotCommandScopeDefault())

# async def setup_bot_commands():
#     bot_commands = [
#         types.BotCommand(command="/help", description="Get info about me"),
#         # BotCommand(command="/qna", description="set bot for a QnA task"),
#         # BotCommand(command="/chat", description="set bot for free chat")
#     ]
#     await bot.set_my_commands(bot_commands)


@dp.message(F.photo, Command('image'))
async def download_photo(message: types.Message, bot: Bot):
    await message.answer(
        "Просматриваем Изображение, это может занять некоторое время, пожалуйста подождите.",
    )
    current_directory = os.getcwd()
    destination=os.path.join(current_directory, "files", f"{message.photo[-1].file_id}.jpg")
    await bot.download(
        message.photo[-1],
        destination=destination
    )
    # print(message)
    # Список для хранения закодированных изображений
    encoded_images = []

    with open(destination, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
        encoded_images.append(encoded_image)

    url = 'http://localhost:11434/api/generate'

    # JSON данные для отправки
    data = {
            "model": "llava",
            # "prompt": ut.translator_func("Это документ? Если это документ, то какой? Стоит ли там печать и подпись?", "en"),
            "prompt": ut.translator_func("Определи тип документа", "en"),
            "stream": False,
            "images": encoded_images,
        }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=data) as response:
            if response.status == 200:
                # Обработка успешного ответа
                response_data = await response.json()
                response = response_data['response']
                answer = ut.translator_func(response)
                # print("Ответ сервера:", answer)
            else:
                # Обработка ошибки
                # print("Произошла ошибка при выполнении запроса:", response.status)
                answer = "Произошла ошибка при выполнении запроса"

    await message.answer(
        text=answer,
        parse_mode=ParseMode.HTML
        )
def no_async_predict(input_message):
    
    client = Client("https://qwen-qwen1-5-72b-chat.hf.space/--replicas/3kh1x/")
    result = client.predict(
        input_message,
        [["None", "None"]],
        "None",
        api_name="/model_chat"
    )
    
    return result[1][1][1]


async def async_predict(input_message):
    
    # client = Client("https://qwen-qwen1-5-72b-chat.hf.space/--replicas/3kh1x/")
    # result = client.predict(
    #     input_message,
    #     [["None", "None"]],
    #     "None",
    #     api_name="/model_chat"
    # )
    
    # return result[1][1][1]
    client = Client("https://qwen-qwen1-5-72b-chat.hf.space/--replicas/3kh1x/")
    loop = asyncio.get_event_loop()
    executor = None  # Подставьте здесь вашего выбора исполнителя, если это необходимо

    result = await loop.run_in_executor(
        executor,
        lambda: client.predict(input_message, [["None", "None"]], "None", api_name="/model_chat")
    )
    return result[1][1][1]


@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        text="Вас рад приветствовать <b>Gemini Patriot</b>\nЯ очень мощный, в моей основе лежат <b>нейросети имеющие 72.3B параметров.</b>\nЯ способен определять класс документа, а так же выводить ключевую информации, прочитав Ваш документ.\nПросто загрузите файл и получите результат.\n<b>Поддерживаемые форматы:\n docx\n doc\n pdf\n rtf\n all_images_formats</b>\n справка: <b>/help</b>", parse_mode=ParseMode.HTML)
    

@dp.message(Command("help"))
@dp.message(CommandStart(
    deep_link=True, magic=F.args == "help"
))

async def cmd_start_help(message: types.Message):
    await message.answer(
"Список доступных команд:\n\n \
<b>Классификация документов</b>\n \
Пример: <b>{{ прикрепите документ, я всё сделаю за вас }}</b>\n\n \
<b>/image</b> - для обработки изображений\n \
Пример: <b>{{ прикрепите изображение }}</b> пометка <b>/image</b>\n\n \
<b>/zip</b> - интелектуальный поиск по архиву\n \
Пример: <b>{{ прикрепите ZIP архив }}</b> пометка <b>/zip {{ Альфа-Банк }}</b>\n\n \
<b>/chat</b> - для общения с языковой моделью\n \
Пример: <b>/chat Привет! Давай дружить!</b>\n\n " ,
parse_mode=ParseMode.HTML
        )


# Если не указать фильтр F.text, 
# то хэндлер сработает даже на картинку с подписью /test
@dp.message(F.text, Command("chat"))
async def any_message(message: types.Message):
    question = message.text.replace("/chat", "")
    await message.answer(
            "Обрабатываем Ваш запрос, пожалуйста подождите.",
        )
    answer = await async_predict(question)

    answer = f"Ваш вопрос: <b>{question}</b>\n\n <b>Ответ:</b> {re.sub(r'[^a-zA-Zа-яА-Я]', ' ', answer)}"
    await message.answer(
        text=answer,
        parse_mode=ParseMode.HTML
        )

@dp.message(Command("zip"))
async def download_doc(message: types.Message):
    query = message.caption.split("/zip")[-1]
    print(query)
    try:
        file_id = message.document.file_id  # Get file id
        file_zip_type = message.document.file_name.split(".")[-1]
        file = await bot.get_file(file_id)  # Get file path
        current_directory = os.getcwd()  # Get current working directory
        if file_zip_type == "zip":
            valid_docs = []
            await message.answer(
"Архив обрабатывается, пожалуйста подождите.\n \
Обработка АРХИВА может занимать больше времени,\n \
чем обработка отдельного документа",
                )
            zip_file_name = os.path.join(current_directory, "files", f"{message.document.file_name}")
            await bot.download_file(file.file_path, zip_file_name)
            docs = ut.extract_zip(zip_file_name)
            

            for item in docs[:10]:
                file_type = item.split(".")[-1]
                # current_directory = os.getcwd()  # Get current working directory
                if file_type == "doc" or file_type == "docx"  or file_type == "pdf" or file_type == "rtf":
                    # file_name = os.path.join(current_directory, "files", f"{message.document.file_name}")
                    # await bot.download_file(file.file_path, file_name)
                    file_name = item.split("/")[-1]
                    if  file_name.endswith(".docx"):
                        text = await ut.read_docx(item)
                    elif file_name.endswith(".doc"):
                        text = await ut.read_doc(item)
                    elif file_name.endswith(".pdf"):
                        text = await ut.read_pdf(item)
                    elif file_name.endswith(".rtf"):
                        text = await ut.read_rtf(item)
                    question=f"классиифицируй тип документа {text}, выведи общее название, найди {query} в документе сделай пометку True если нашёл"
                    answer = no_async_predict(question)
                    index = str(answer).find("True")  # Находим индекс первого вхождения "True" в тексте
                    if index != -1:
                        print(f"Строка 'True' найдена в тексте на позиции {index}.")
                        # Ваш словарь ключ-значение
                        dictionary = {
                            "доверенность": "proxy",
                            "договор": "contract",
                            "передаточный акт": "act",
                            "акт": "act",
                            "заявление": "application",
                            "приказ": "order",
                            "расчет": "invoice",
                            "накладная": "invoice",
                            "форма": "invoice",
                            "счет": "bill",
                            "приложение": "bill",
                            "счет-оферта": "bill",
                            "фактура": "bill",
                            "(фактура)": "bill",
                            "faktura": "bill",
                            "соглашение": "arrangement",
                            "договор оферты": "contract offer",
                            "оферта": "contract offer",
                            "устав": "statute",
                            "решение": "determination"
                        }

                        # Ваша строка
                        your_string = answer.lower()

                        # Разделить строку на слова по пробелам и итерировать
                        for word in your_string.split():
                            # Проверить, есть ли слово в качестве ключа в словаре
                            if word in dictionary:
                                # Если да, вернуть значение для этого ключа
                                found_value = dictionary[word]
                                break
                        
                        found_value = found_value if "found_value" in locals() else None
                        valid_docs.append((str(file_name)) + "  " + f"Тип документа: {found_value}")
                    else:
                        print("Строка 'True' не найдена в тексте.")
                else:
                    continue
            print(valid_docs)
            answer = f"<b>Документы удовлетворящие параметрам запроса {query}: </b> {'|__|'.join(valid_docs)}"
            await message.answer(
                text=answer,
                parse_mode=ParseMode.HTML
                )
        # else:
        #     await message.answer(
        #         text="Убедитесь, что файл имеет расширение .doc, .docx, .rtf или .pdf")
    except AttributeError:
        await message.answer(
                text="Убедитесь, что файл имеет расширение .zip")


# @dp.message(Command("doc"))
@dp.message()
async def download_doc(message: types.Message):
    try:
        file_id = message.document.file_id  # Get file id
        file_type = message.document.file_name.split(".")[-1]
        file = await bot.get_file(file_id)  # Get file path
        current_directory = os.getcwd()  # Get current working directory
        if file_type == "doc" or file_type == "docx"  or file_type == "pdf" or file_type == "rtf":
            await message.answer(
                "Документ обрабатывается, пожалуйста подождите.",
                )
            file_name = os.path.join(current_directory, "files", f"{message.document.file_name}")
            await bot.download_file(file.file_path, file_name)
            if  message.document.file_name.endswith(".docx"):
                text = await ut.read_docx(file_name)
            elif message.document.file_name.endswith(".doc"):
                text = await ut.read_doc(file_name)
            elif message.document.file_name.endswith(".pdf"):
                text = await ut.read_pdf(file_name)
            elif message.document.file_name.endswith(".rtf"):
                text = await ut.read_rtf(file_name)
            # question = f"Классиифицируй и сообщи только тип документа: {text}"
            question = f"классиифицируй типы документов, выведи только общее названия типов и ключевые данные, если есть: {text}"
            answer = await async_predict(question)
            # Ваш словарь ключ-значение
            dictionary = {
                "доверенность": "proxy",
                "договор": "contract",
                "передаточный акт": "act",
                "акт": "act",
                "заявление": "application",
                "приказ": "order",
                "расчет": "invoice",
                "накладная": "invoice",
                "форма": "invoice",
                "счет": "bill",
                "приложение": "bill",
                "счет-оферта": "bill",
                "фактура": "bill",
                "(фактура)": "bill",
                "faktura": "bill",
                "соглашение": "arrangement",
                "договор оферты": "contract offer",
                "оферта": "contract offer",
                "устав": "statute",
                "решение": "determination"
            }

            # Ваша строка
            your_string = answer.lower()

            # Разделить строку на слова по пробелам и итерировать
            for word in your_string.split():
                # Проверить, есть ли слово в качестве ключа в словаре
                if word in dictionary:
                    # Если да, вернуть значение для этого ключа
                    found_value = dictionary[word]
                    break
            
            found_value = found_value if "found_value" in locals() else None
            # answer = f"Документ <b>{message.document.file_name}</b>:\n\n{re.sub(r'[^a-zA-Zа-яА-Я]', ' ', answer)} \n\n <b>Тип документа: {found_value}</b>"
            answer = f"Документ <b>{message.document.file_name}</b>:\n\n{answer} \n\n <b>Тип документа: {found_value}</b>"
            await message.answer(
                text=answer,
                parse_mode=ParseMode.HTML
                )
        else:
            await message.answer(
                text="Убедитесь, что файл имеет расширение .doc, .docx, .rtf или .pdf")
    except AttributeError:
        await message.answer(
                text="Убедитесь, что файл имеет расширение .doc, .docx, .rtf или .pdf")
    # await message.answer(
    #             text="Убедитесь, что файл имеет расширение .doc или .docx")



async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)


if __name__ == "__main__":
    # client = Client("https://qwen-qwen1-5-72b-chat.hf.space/--replicas/3kh1x/")
    asyncio.run(main())