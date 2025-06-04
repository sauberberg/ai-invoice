import os
import fitz  # PyMuPDF for PDF text extraction
import pytesseract
from PIL import Image
import streamlit as st
from dotenv import load_dotenv

# Загрузка переменных окружения (например, OPENAI_API_KEY) из .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Настройка страницы Streamlit
st.set_page_config(page_title="AI Accounting", layout="wide")

st.title("AI Accounting")

# Форма ввода пользовательских данных
with st.form(key="input_form"):
    st.subheader("Параметры анализа")
    country = st.selectbox("Выберите страну", ["Германия", "Польша", "Франция", "Италия"])
    company_type = st.selectbox("Тип компании", ["GmbH", "Freelancer", "SAS", "SRL"])
    vat_registered = st.radio("НДС зарегистрирован?", ["Да", "Нет"], index=1)
    language = st.selectbox("Язык ответа", ["Deutsch", "English", "Français", "Polski"])
    uploaded_file = st.file_uploader("Загрузите документ (PDF, JPG или PNG)", type=["pdf", "png", "jpg", "jpeg"])
    manual_text = st.text_area("Или введите текст вручную")
    submit = st.form_submit_button("Продолжить")

# Обработка нажатия на кнопку "Продолжить"
if submit:
    # Проверка наличия входных данных (файл или текст)
    if not uploaded_file and not manual_text:
        st.error("Пожалуйста, загрузите файл или введите текст для анализа.")
        st.stop()

    # Извлечение текста из загруженного файла, если он предоставлен
    extracted_text = ""
    if uploaded_file:
        file_name = uploaded_file.name.lower()
        try:
            if file_name.endswith(".pdf"):
                # Чтение PDF-файла и извлечение текста со всех страниц
                file_bytes = uploaded_file.read()
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                for page in doc:
                    extracted_text += page.get_text("text")
                doc.close()
            else:
                # Обработка изображения: использование Tesseract OCR
                image = Image.open(uploaded_file)
                # Если выбран язык не English, указываем соответствующий язык для OCR
                tess_lang = ""
                if language == "Deutsch":
                    tess_lang = "deu"
                elif language == "Français":
                    tess_lang = "fra"
                elif language == "Polski":
                    tess_lang = "pol"
                else:
                    tess_lang = "eng"
                extracted_text = pytesseract.image_to_string(image, lang=tess_lang)
        except Exception as e:
            st.error(f"Ошибка при извлечении текста: {e}")
            st.stop()

    # Если текст введён вручную, используем его
    input_text = ""
    if manual_text:
        input_text = manual_text
    # Если был и файл, и текст, объединяем их (например, если пользователь хочет дополнить OCR-текст своим вводом)
    if extracted_text and input_text:
        input_text = extracted_text.strip() + "\n" + input_text.strip()
    elif extracted_text:
        input_text = extracted_text

    # Проверяем, получен ли текст для анализа
    if not input_text:
        st.error("Не удалось получить текст для анализа. Проверьте входные данные.")
        st.stop()

    # Формирование запроса для модели GPT
    # Включаем параметры: страна, тип компании, НДС и язык ответа
    prompt = (
        f"Страна: {country}\n"
        f"Тип компании: {company_type}\n"
        f"НДС зарегистрирован: {vat_registered}\n"
        f"Задание: Проанализируй текст документа и предоставь краткое резюме и рекомендации. "
        f"Ответь на языке: {language}.\n"
        f"Текст документа:\n\"\"\"\n{input_text}\n\"\"\""
    )

    # Проверка наличия API-ключа OpenAI
    if not OPENAI_API_KEY:
        st.error("API-ключ OpenAI не найден. Укажите OPENAI_API_KEY в файле .env или в настройках.")
        st.stop()

    # Инициализация модели OpenAI через LangChain
    try:
        # Попытка импорта для новой структуры langchain
        from langchain_openai import ChatOpenAI
    except ImportError:
        # Импорт для старых версий langchain
        from langchain.chat_models import ChatOpenAI
    # Создание экземпляра чата (GPT-3.5-Turbo по умолчанию)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY, temperature=0.0)
    
    # Вызов модели для получения ответа
    try:
        # Используем один промпт, модель ожидает список сообщений (система + пользователь)
        from langchain.schema import SystemMessage, HumanMessage
        system_msg = SystemMessage(content=f"You are a helpful assistant. Provide the answer in {language}.")
        user_msg = HumanMessage(content=prompt)
        ai_response = llm([system_msg, user_msg])
        result_text = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
    except Exception as e:
        st.error(f"Ошибка при обращении к модели OpenAI: {e}")
        st.stop()

    # Отображение результата в приложении
    st.subheader("Результат анализа")
    st.write(result_text)

    # Формирование файла с результатами для скачивания
    output_lines = []
    output_lines.append("### Резюме и рекомендации\n")
    output_lines.append(result_text.strip())
    output_content = "\n".join(output_lines)
    # Кнопка для скачивания результата
    st.download_button(
        label="Скачать результаты (.txt)",
        data=output_content,
        file_name="analysis_result.txt",
        mime="text/plain"
    )
