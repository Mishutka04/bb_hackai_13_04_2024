import os
import docx2txt  # Для чтения .doc файлов
import textract
import re
import docx
import asyncio
import translators as ts
from pypdf import PdfReader
from striprtf.striprtf import rtf_to_text


async def clean_text(text):
    # Удаление всех символов, кроме букв и цифр
    cleaned_text = re.sub(r'[^a-zA-Z0-9а-яА-Я\s]', '', text)
    # Удаление лишних пробелов
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = cleaned_text.lower()
    return cleaned_text[:8000]

# Функция для чтения текста из файлов .docx
async def read_docx(file_path):
    doc = docx.Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text
    text = await clean_text(text)
    return text

# Функция для чтения текста из файлов .doc
async def read_doc(file_path):
    text = textract.process(file_path)
    text = text.decode("utf-8")
    text = await clean_text(text)
    return text

async def read_pdf(file_path):
    reader = PdfReader(file_path)
    number_of_pages = len(reader.pages)
    page = reader.pages[0]
    text = page.extract_text()
    print(text)
    text = await clean_text(text)
    return text


async def read_rtf(file_path):
    with open(file_path, 'r') as file:
        text = file.read()
    text = rtf_to_text(text)
    text = await clean_text(text)
    return text

def translator_func(text, to_language="ru"):
    translator = "bing"
    ts_text = ts.translate_text(
                  text,
                  translator=translator,
                  to_language=to_language)
    return ts_text

