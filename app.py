import streamlit as st
from dotenv import load_dotenv
import os

# Загрузка переменных окружения (.env)
load_dotenv()

from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

st.set_page_config(page_title="Invoice AI", layout="centered")

st.title("🌍 AI Multi-country Accounting")
country = st.selectbox("Страна", ["Германия", "Польша", "Франция", "Италия"])
company_type = st.selectbox("Тип юр. лица", ["GmbH", "Freelancer", "SAS", "SRL"])
vat = st.selectbox("Плательщик НДС?", ["Да", "Нет"])
language = st.selectbox("Язык", ["Deutsch", "English", "Français", "Polski"])

file = st.file_uploader("Загрузите PDF/JPG/PNG", type=["pdf", "jpg", "png"])
invoice_text = st.text_area("Или вставьте OCR-текст", height=140)

# Промт для AI
prompt = PromptTemplate.from_template("""
Страна: {country}
Юр. лицо: {company_type}
VAT: {vat}
Язык: {language}

Извлеки из инвойса ключевые поля для отчёта по законам страны. Верни JSON.

Текст инвойса:
{invoice_text}
""")

# Важно! Укажи явно openai_api_key и укажи модель (gpt-4o или gpt-3.5-turbo)
llm = ChatOpenAI(
    model="gpt-4o", 
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

chain = LLMChain(llm=llm, prompt=prompt)

# Основная AI-кнопка
if st.button("Извлечь данные AI"):
    with st.spinner("AI-обработка..."):
        if not invoice_text.strip():
            st.error("Пожалуйста, вставьте OCR-текст инвойса!")
        else:
            result = chain.run(
                country=country,
                company_type=company_type,
                vat=vat,
                language=language,
                invoice_text=invoice_text
            )
            st.success("✅ Данные извлечены AI!")
            st.json(result)
