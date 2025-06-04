import os
import streamlit as st
from dotenv import load_dotenv

import fitz  # PyMuPDF for PDF text extraction
from PIL import Image
import pytesseract

# 1. Загрузка переменных окружения
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 2. UI
st.set_page_config(page_title="Invoice AI", layout="centered")
st.title("🌍 AI Multi-country Accountant")

with st.form(key="input_form"):
    country = st.selectbox("Страна", ["Германия", "Польша", "Франция", "Италия"])
    company_type = st.selectbox("Тип юр. лица", ["GmbH", "Freelancer", "SAS", "SRL"])
    vat = st.radio("Плательщик НДС?", ["Да", "Нет"])
    language = st.selectbox("Язык", ["Deutsch", "English", "Français", "Polski"])
    uploaded_file = st.file_uploader("Загрузите PDF/JPG/PNG", type=["pdf", "jpg", "png", "jpeg"])
    manual_text = st.text_area("Или введите текст вручную", height=140)
    submit = st.form_submit_button("Продолжить")

# 3. Вспомогательные функции
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text("text")
        doc.close()
    except Exception as e:
        st.warning(f"Ошибка чтения PDF: {e}")
    return text.strip()

def extract_text_from_image(image_file, lang_code):
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image, lang=lang_code)
    except Exception as e:
        st.warning(f"Ошибка OCR: {e}")
        text = ""
    return text.strip()

# 4. Мэппинг языков для OCR и LLM
ocr_langs = {"Deutsch": "deu", "English": "eng", "Français": "fra", "Polski": "pol"}

# 5. Обработка сабмита формы
if submit:
    # 5.1 Проверка входа
    if not uploaded_file and not manual_text:
        st.error("Пожалуйста, загрузите файл или введите текст.")
        st.stop()

    extracted_text = ""
    if uploaded_file:
        file_name = uploaded_file.name.lower()
        if file_name.endswith(".pdf"):
            extracted_text = extract_text_from_pdf(uploaded_file)
        else:
            extracted_text = extract_text_from_image(uploaded_file, ocr_langs.get(language, "eng"))

    # Если оба есть — дополняем
    input_text = extracted_text.strip()
    if manual_text:
        if input_text:
            input_text += "\n" + manual_text.strip()
        else:
            input_text = manual_text.strip()

    # 5.2 Контроль финального текста
    if not input_text:
        st.error("Не удалось получить текст для анализа. Проверьте входные данные.")
        st.stop()

    # 5.3 Формируем промпт
    prompt = (
        f"Страна: {country}\n"
        f"Тип компании: {company_type}\n"
        f"НДС зарегистрирован: {vat}\n"
        f"Задание: Проанализируй текст документа, выведи резюме, предложи бухгалтерские рекомендации, и сформулируй actionable insights для бизнеса. "
        f"Ответь на языке: {language}.\n"
        f"Текст документа:\n\"\"\"\n{input_text}\n\"\"\""
    )

    # 5.4 Проверка ключа
    if not OPENAI_API_KEY:
        st.error("API-ключ OpenAI не найден. Укажите OPENAI_API_KEY в .env.")
        st.stop()

    # 5.5 Вызов OpenAI через langchain-openai (или fallback на старый)
    try:
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            from langchain.chat_models import ChatOpenAI

        llm = ChatOpenAI(
            model_name="gpt-4o",  # Или gpt-3.5-turbo, если gpt-4o не доступен
            openai_api_key=OPENAI_API_KEY,
            temperature=0.0
        )

        from langchain.schema import SystemMessage, HumanMessage
        system_msg = SystemMessage(content=f"You are a professional accountant for EU companies. Answer in {language}.")
        user_msg = HumanMessage(content=prompt)
        ai_response = llm([system_msg, user_msg])
        result_text = ai_response.content if hasattr(ai_response, "content") else str(ai_response)
    except Exception as e:
        st.error(f"Ошибка OpenAI: {e}")
        st.stop()

    # 5.6 Вывод результата и рекомендации
    st.subheader("Результат анализа и рекомендации")
    st.write(result_text)

    st.download_button(
        label="Скачать рекомендации (.txt)",
        data=result_text,
        file_name="ai_invoice_recommendations.txt",
        mime="text/plain"
    )
