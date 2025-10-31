import base64
import streamlit as st

from pathlib import Path
from dotenv import load_dotenv
from files.py.functions import init_session_state, request
import streamlit.components.v1 as components

# Загрузить .env
load_dotenv()


st.markdown("""
<style>
header[data-testid="stHeader"] { height: 0; visibility: hidden; }   /* можно убрать, если нужен штатный хедер */
div[data-testid="stAppViewContainer"] > .main { padding-top: 0 !important; }

/* Верхняя полоса внутри контент-колонки (в обычном потоке, без fixed) */
.page-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 0;         /* уменьшенный вертикальный зазор */
}

/* Кнопка справа */
.page-top .btn {
  display: inline-block;
  padding: 8px 14px;
  border: 1px solid rgba(49,51,63,.25);
  border-radius: 6px;
  text-decoration: none;
  font-weight: 600;
  white-space: nowrap;     /* без переноса на мобилках */
  background: var(--background-color);
  color: var(--text-color);
  box-shadow: 0 1px 2px rgba(0,0,0,.06);
}
.page-top .btn:hover { filter: brightness(.97); }
</style>
""", unsafe_allow_html=True)





st.markdown(
        '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">',
        unsafe_allow_html=True)
img_bytes = Path("files/png/DISg_colored.png").read_bytes()
encoded_img = base64.b64encode(img_bytes).decode()
img_html = "data:image/png;base64,{}".format(encoded_img)
st.markdown(f"""
<div class="page-top">
    <a href="https://jira.data-integration.ru/plugins/servlet/desk">
        <img src="{img_html}" width=30 class="navbar-brand" target="_blank"></img>
    </a>
    <div id="fixed-logout">
        <form method="get">
            <input type="hidden" name="logout" value="true">
            <button>Выйти</button>
        </form>
    </div>
</div>
""", unsafe_allow_html=True)

# st.markdown(f"""
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
    layout="wide",
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

