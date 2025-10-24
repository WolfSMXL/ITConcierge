import base64
import streamlit as st

from pathlib import Path
from dotenv import load_dotenv
from files.py.functions import init_session_state, request

# Загрузить .env
load_dotenv()

# Лого DIS Group в левом верхнем углу с ссылкой на jira
st.markdown(
        '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">',
        unsafe_allow_html=True)
img_bytes = Path("files/png/DISg_colored.png").read_bytes()
encoded_img = base64.b64encode(img_bytes).decode()
img_html = "data:image/png;base64,{}".format(encoded_img)
#st.markdown(f"""
#   <nav class="navbar fixed-top navbar-expand-lg navbar-dark">
#      <a href="https://jira.data-integration.ru/plugins/servlet/desk">
#        <img src="{img_html}" width=30 class="navbar-brand" target="_blank"></img>
#      </a>
#    </nav>
#    """, unsafe_allow_html=True)

# Скрыть цветную линию от Streamlit
hide_decoration_bar_style = '''
    <style>
        [data-testid="stDecoration"] {
            display: none;
        }
    </style>
'''
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

# Настроить название страницы и логотип в заголовке обозревателя
st.set_page_config(
    page_title="DIS Help",
    page_icon="files/ico/DISg_colored.ico",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS для изменения цвета кнопки формы
st.markdown("""
<style>
    .stButton>button {
        background-color: #00add7; /* DIS */
        color: white;
        border: none;
        padding: 10px 24px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 8px;
    }
    .stButton>button:hover {
        background-color: #002f55; /* Темно-синий при наведении */
        color: #2c75ff;
    }
</style>
""", unsafe_allow_html=True)

# Инициализировать сессию
init_session_state()

# Открыть страницу
request("")
