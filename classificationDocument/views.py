import os
import uuid

from django.contrib import messages
from django.shortcuts import render
from django.views.generic.edit import FormView
from .forms import FileFieldForm

import os
import docx2txt  # Для чтения .doc файлов
import textract
import re
import docx
import asyncio
import translators as ts
from pypdf import PdfReader
from striprtf.striprtf import rtf_to_text

from gradio_client import Client


def doc(doc):
    client = Client("https://qwen-qwen1-5-72b-chat.hf.space/--replicas/3kh1x/")
    dox = f"классиифицируй типы документов, выведи только общее названия типов и ключевые данные, если есть: {doc}"

    result = client.predict(
        dox,  # str  in 'Input' Textbox component
        [["None", "None"], ],
        # Tuple[str | Dict(file: filepath, alt_text: str | None) | None, str | Dict(file: filepath, alt_text: str | None) | None]  in 'Qwen1.5-72B-Chat' Chatbot component
        "None",  # str  in 'parameter_9' Textbox component
        api_name="/model_chat"
    )
    print(result[1][1][1])

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
    your_string = result[1][1][1].lower()

    # Разделить строку на слова по пробелам и итерировать
    for word in your_string.split():
        # Проверить, есть ли слово в качестве ключа в словаре
        if word in dictionary:
            # Если да, вернуть значение для этого ключа
            found_value = dictionary[word]
            break

    # Печать найденного значения (если совпадение найдено) или None (если совпадение не найдено)
    print(found_value if "found_value" in locals() else None)
    return (found_value if "found_value" in locals() else None)


def clean_text(text):
    # Удаление всех символов, кроме букв и цифр
    cleaned_text = re.sub(r'[^a-zA-Z0-9а-яА-Я\s]', '', text)
    # Удаление лишних пробелов
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = cleaned_text.lower()
    return cleaned_text[:8000]


# Функция для чтения текста из файлов .docx
def read_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text
    text = clean_text(text)
    return text


# Функция для чтения текста из файлов .doc
def read_doc(file_path):
    text = textract.process(file_path)
    text = text.decode("utf-8")
    text = clean_text(text)
    return text


def read_pdf(file_path):
    reader = PdfReader(file_path)
    page = reader.pages[0]
    text = page.extract_text()
    text = clean_text(text)
    return text


def read_rtf(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    text = rtf_to_text(text)
    text = clean_text(text)
    return text


def translator_func(text, to_language="ru"):
    translator = "bing"
    ts_text = ts.translate_text(
        text,
        translator=translator,
        to_language=to_language)
    return ts_text


def read_text(file, ext):
    if ext == ".doc" or ext == ".docx" or ext == ".pdf" or ext == ".rtf":
        file_name = os.path.join(file)
        if ext == ".docx":
            text = read_docx(file_name)
        elif ext == ".doc":
            text = read_doc(file_name)
        elif ext == ".pdf":
            text = read_pdf(file_name)
        elif ext == ".rtf":
            text = read_rtf(file_name)
        return text
    else:
        return "-"


def handle_uploaded_file(f):
    name = f.name
    ext = ''

    if '.' in name:
        ext = name[name.rindex('.'):]
        name = name[:name.rindex('.')]

    suffix = str(uuid.uuid4())
    with open(f"uploads/{name}_{suffix}{ext}", "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)

            print(type(destination))
            # read_text(destination, ext)
        return read_text(f"uploads/{name}_{suffix}{ext}", ext)


class FileFieldFormView(FormView):
    form_class = FileFieldForm
    template_name = "classificationDocument/upload.html"  # Replace with your template.
    success_url = "..."  # Replace with your URL or reverse().

    def form_valid(self, form):
        files = form.cleaned_data["file_field"]
        messages.success(self.request, 'The post has been created successfully.')
        file_name = ''
        answer = ""
        for f in files:
            text = handle_uploaded_file(f)
            answer = doc(text)
            file_name = f.name
            # print(text)
            ...  # Подключение модулей для обработки
        return render(self.request, 'classificationDocument/info_file.html',
                      context={'file': file_name, 'answer': answer})
