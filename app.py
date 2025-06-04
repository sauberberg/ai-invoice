import streamlit as st
# from dotenv import load_dotenv
# load_dotenv()

st.set_page_config(page_title="Invoice AI", layout="centered")

st.title("🌍 AI Multi-country Accountant")
country = st.selectbox("Страна", ["Германия", "Польша", "Франция", "Италия"])
company_type = st.selectbox("Тип юр. лица", ["GmbH", "Freelancer", "SAS", "SRL"])
vat = st.selectbox("Плательщик НДС?", ["Да", "Нет"])
language = st.selectbox("Язык", ["Deutsch", "English", "Français", "Polski"])

file = st.file_uploader("Загрузите PDF/JPG/PNG", type=["pdf", "jpg", "png"])
invoice_text = st.text_area("Или вставьте OCR-текст", height=140)

if st.button("Продолжить"):
    st.success("UI работает! Следующий шаг — подключение AI.")
