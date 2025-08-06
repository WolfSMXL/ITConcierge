import base64
import os
from pathlib import Path

import streamlit as st
from streamlit import session_state
from streamlit_cookies_manager import EncryptedCookieManager
from streamlit.components.v1 import html
from time import sleep, time
from jira import JIRA
import xml.etree.ElementTree as ET
import psycopg2

st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)
img_bytes = Path("files/png/DISg_colored.png").read_bytes()
encoded_img = base64.b64encode(img_bytes).decode()
img_html = "data:image/png;base64,{}".format(encoded_img)
st.markdown(f"""
<nav class="navbar fixed-top navbar-expand-lg navbar-dark">
  <a href="https://www.dis-group.ru">
    <img src="{img_html}" width=30 class="navbar-brand" target="_blank"></img>
  </a>
</nav>
""", unsafe_allow_html=True)

# Настроить название страницы и логотип в заголовке обозревателя
st.set_page_config(
    page_title="Admin, Help!",
    page_icon="files/ico/DISg_colored.ico",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Настроить логотип в левом верхнем углу экрана обозревателя
# st.logo(
#     image="files/png/DISg_colored.png",
#     size="large",
#     link="https://www.dis-group.ru",
#     icon_image="files/ico/DISg_colored.ico")

# CSS для изменения цвета кнопки формы
st.markdown("""
<style>
    .stFormSubmitButton>button {
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
    .stFormSubmitButton>button:hover {
        background-color: #002f55; /* Темно-синий при наведении */
        color: #2c75ff;
    }
</style>
""", unsafe_allow_html=True)

# Соединение с Jira
if 'jira' not in st.session_state: st.session_state.jira = None
# Статус заявки
if not 'заявка' in st.session_state: st.session_state.заявка = False
# Счётчик попыток создания заявок в одном сеансе
if not 'счётчик' in st.session_state: st.session_state.счётчик = 0
# Текст заявки
if not 'текст_заявки' in st.session_state:
    st.session_state.текст_заявки = ''
# Статус аутентификации
if not 'аутентификация' in st.session_state:
    st.session_state.аутентификация = True
# Статус заявки
if not 'заявка_отправлена' in st.session_state:
    st.session_state.заявка_отправлена = False
# Название проблемного объекта
if not 'объект' in st.session_state:
    st.session_state.объект = st.query_params.get('объект', None)
# Пользователь
if not 'пользователь' in st.session_state:
    st.session_state.пользователь = st.query_params.get(
        'пользователь', "Аноним")
# Имя пользователя
if not 'имя_пользователя' in st.session_state:
    st.session_state.имя_пользователя = "Аноним"
# Обработка выхода
if "logout" not in st.session_state:
    st.session_state.logout = False
query_params = st.query_params
if query_params.get("logout") == "true":
    st.session_state.logout = True

def Отправить_заявку(текст: str, файлы: list) -> None:
    jj = st.session_state.jira
    projects = JIRA.projects(st.session_state.jira)
    st.empty()  # В работе
    return None


def Объект_проверка() -> bool:
    """Процедура проверяет - выбран проблемный объект или нет.
    Возвращает `True` если выбран. Иначе - `False`"""
    возврат = False
    try:
        if st.session_state.объект: возврат = True
    except:
        st.empty()
    finally:
        return возврат


def Сборка_текста_заявки() -> None:
    """Процедура собирает текст заявки из полей формы"""
    st.session_state.текст_заявки = ""
    i = 1
    for _ in ПРОБЛЕМЫ["Техподдержка"]:
        if _ in st.session_state.проблемы:
            if i == 1: st.session_state.текст_заявки += "В техподдержку:\n\n"
            st.session_state.текст_заявки += str(i) + ") " + _ + "\n"
            i += 1
    i = 1
    for _ in ПРОБЛЕМЫ["Обслуживание"]:
        if _ in st.session_state.проблемы:
            if i == 1: st.session_state.текст_заявки += \
                "\nОбслуживающему персоналу:\n\n"
            st.session_state.текст_заявки += str(i) + ") " + _ + "\n"
            i += 1

    if st.session_state.предложить_улучшение:
        st.session_state.текст_заявки += "\nПредлагается улучшение:\n\n" + \
                                         st.session_state.предложить_улучшение.strip() + "\n\n"
        i += 1
    if st.session_state.другое:
        st.session_state.текст_заявки += "\nДругие предложения:\n\n" + \
                                         st.session_state.другое.strip()
    return None


def Проверка_полей() -> bool:
    """Процедура проверяет заполнение полей заявки и возвращает `True`,
    если поля заполнялись. В ином случае возвращает `False`"""
    возврат = False
    if st.session_state.текст_заявки:
        возврат = True
    elif len(st.session_state.файлы):
        возврат = True
    return возврат


def Проверки() -> None:
    """Процедура выполняет проверки заполнения полей формы, выбора
    проблемных объектов и сведений о пользователе. В тех случаях, когда
    отсутствуют исходные данные (наименование проблемного объекта,
    отсутствуют какие-либо сведения о проблемах и не приложен ни один
    файл) процедура переводит значение статуса заявки в состояние False
    """
    # Проверка выбора объекта
    if Объект_проверка():
        st.info("Проблемный объект: " + st.session_state.объект)
        sleep(3)
        st.session_state.заявка = True
    else:
        st.warning("Необходимо выбрать проблемный объект!")
        sleep(3)
        st.session_state.заявка = False
    # Проверка заполнения полей заявки
    if (not st.session_state.текст_заявки == "") or \
            (not len(st.session_state.файлы)):
        if st.session_state.текст_заявки:
            st.info("Текст заявки: \n" + st.session_state.текст_заявки)
        if len(st.session_state.файлы):
            st.info("Добавлено файлов: " + \
                    str(len(st.session_state.файлы)))
        sleep(3)
        st.session_state.заявка = True
    else:
        st.warning("Необходимо заполнить поля заявки!")
        sleep(3)
        st.session_state.заявка = False
    return None


# Создание экземпляра менеджера куков
cookies = EncryptedCookieManager(
    prefix=st.secrets["Крошки"]["префикс"],
    password=os.environ.get("COOKIES_PASSWORD", st.secrets["Крошки"]["пароль"])
)

if not cookies.ready():
    st.spinner("Ожидание загрузки хлебных крошек", show_time=True)
    st.stop()


def Аутентификация() -> bool:
    """Процедура аутентификации пользователя в Jira.
    При нахождении пользователя в системе возвращает True.
    В обратном случае возвращает False"""
    возврат = False
    # Проверка имени пользователя и пароля
    try:
        st.session_state.jira = JIRA(
            options={"server": "https://jira.data-integration.ru"},
            basic_auth=(
                st.session_state.имя_пользователя,
                st.session_state.пароль_пользователя)
        )

        if 'пользователь_информация' not in st.session_state:
            st.session_state.пользователь_информация = \
                st.session_state.jira.myself()
        st.session_state.пользователь = \
            st.session_state.пользователь_информация.get(
                'displayName', "Аноним")
        возврат = True
    except Exception as e:
        st.empty()
        #st.error("Отказ в аутентификации пользователя:"+str(e))
        # sleep(3)
    finally:
        return возврат


# Если пользователь не аутентифицирован, показываем форму входа
if Аутентификация():
    st.empty()
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2.form("auth_form"):
        st.image("files/png/Jira.webp", use_container_width=True)
        st.session_state.имя_пользователя = st.text_input("Имя")
        st.session_state.пароль_пользователя = st.text_input("Пароль", type="password")
        remember_me = st.checkbox("Запомнить")
        submit_button = st.form_submit_button(
            "Вход", use_container_width=True)
        if submit_button:
            if Аутентификация():
                st.session_state.аутентификация = True
                if remember_me:
                    # Устанавливаем cookie с сроком действия 30 дней
                    cookies['authenticated'] = 'true'
                    cookies['username'] = st.session_state.имя_пользователя
                    expires_at = int(time()) + 30 * 24 * 60 * 60  # 30 дней
                    cookies['expires_at'] = str(expires_at)
                    cookies.save()
                    # Обновляем страницу, чтобы скрыть форму входа
                st.rerun()
            else:
                st.error("Неверное имя пользователя или пароль")

# Если пользователь аутентифицирован, показываем основное содержимое
else:
    # Кнопка, встроенная через HTML-форму + query-параметр
    st.markdown("""
    <style>
    #fixed-logout {
        position: fixed;
        top: 10px;
        right: 20px;
        z-index: 9999;
    }
    #fixed-logout button {
        font-weight: bold;
        padding: 8px 16px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
    }
    </style>

    <div id="fixed-logout">
        <form method="get">
            <input type="hidden" name="logout" value="true">
            <button type="submit">Выйти</button>
        </form>
    </div>
    """, unsafe_allow_html=True)
    st.session_state.logout = False
    col1, col2 = st.columns([1, 0.13])
    st.header(f"Добро пожаловать, {st.session_state.пользователь}!")
    # Обработка выхода
    if st.session_state.logout:
        # Сброс данных сессии
        st.session_state.аутентификация = False
        cookies['authenticated'] = 'false'
        cookies['username'] = ''
        cookies['expires_at'] = '0'
        print("worked")
        cookies.save()

    conn = psycopg2.connect(dbname='postgres', user='postgres',
                            password='postgres', host='localhost', port='5432')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM itconcierge."Objects"')
    objects = cursor.fetchall()
    cursor.execute('SELECT * FROM itconcierge."Problems" where problem_type in (\'Обслуживание\')')
    service_problems = cursor.fetchall()
    cursor.execute('SELECT * FROM itconcierge."Problems" where problem_type in (\'Техническая\')')
    technical_problems = cursor.fetchall()
    cursor.close()
    conn.close()
    ОБЪЕКТЫ = []
    technical_problems_arr = []
    service_problems_arr = []
    for i in objects:
        ОБЪЕКТЫ.append(i[1])
    for i in service_problems:
        service_problems_arr.append(i[2])
    for i in technical_problems:
        technical_problems_arr.append(i[2])
    # ОБЪЕКТЫ = [
    #     "Переговорная «Алматы»",
    #     "Переговорная «Тель-Авив»",
    #     "Переговорная «Санкт-Петербург»",
    #     "Кабинет Лихницкого П.В.",
    #     "Кабинет Гиацинтова О.М.",
    #     "Кабинет Косилова А.Е.",
    #     "Кабинет Нечипоренко Е.Н.",
    #     "Кабинет Финка Д.Н.",
    #     "Принтер Бухгалтерия",
    #     "Принтер HR",
    #     "Принтер Sales",
    #     "Принтер Reception",
    #     "Принтер Back Office",
    # ]
    ПРОБЛЕМЫ = dict()
    ПРОБЛЕМЫ["Техподдержка"] = technical_problems_arr
    ПРОБЛЕМЫ["Обслуживание"] = service_problems_arr
    # ПРОБЛЕМЫ = {
    #     "Техподдержка": [
    #         "Проблемы с оборудованием",
    #         "Нет бумаги в принтере",
    #         "Замена картриджа в принтере",
    #         "Не работает ВКС",
    #         "Интернет сбой", ],
    #     "Обслуживание": [
    #         "Нет питьевой воды",
    #         "Необходима уборка",
    #     ]}

    if (not st.session_state.заявка_отправлена) and \
            (not st.session_state.заявка):
        with st.form('форма_заявка'):
            if not Объект_проверка():
                st.session_state.объект = st.segmented_control(
                    "Выберите объект",
                    options=ОБЪЕКТЫ)
                st.divider()
            else:
                if (not st.session_state.пользователь) or \
                        (st.session_state.пользователь == "Аноним"):
                    st.subheader(
                        st.session_state.объект,
                        divider=True)
                else:
                    слева, справа = st.columns([1, 1])
                    слева.caption(st.session_state.объект)
                    #справа.caption(f"Добро пожаловать, {st.session_state.пользователь}!")
            st.pills("Причина обращения", key='проблемы',
                     options=ПРОБЛЕМЫ["Техподдержка"] + ПРОБЛЕМЫ["Обслуживание"],
                     selection_mode="multi")
            слева, справа = st.columns([1, 1])
            слева.text_area("Предложить улучшение",
                            key="предложить_улучшение")
            справа.text_area("Другое", key="другое")
            слева.text_input("Обратная связь", key="пользователь_телефон",
                             placeholder="Укажите телефон для обратной связи")
            справа.text_input("Электропочта", key="пользователь_электропочта",
                              placeholder="Адрес электронной почты",
                              label_visibility="hidden")
            st.file_uploader("Добавить вложение",
                             key="файлы",
                             type=["jpg", "jpeg", "png", "pdf", "doc",
                                   "docx", "xls", "xlsx"],
                             accept_multiple_files=True)
            if st.form_submit_button("Отправить заявку"):
                Сборка_текста_заявки()
                if not Объект_проверка():
                    st.error("Не выбран объект!")
                    sleep(1)
                else:
                    if not Проверка_полей():
                        st.error("Форма не заполнена!")
                        sleep(1)
                    else:
                        st.info("Проверки выполнены...")
                        st.info(st.session_state.текст_заявки)
                        st.info("Приложенных файлов: " + \
                                str(len(st.session_state.файлы)))
                        Отправить_заявку(st.session_state.текст_заявки, st.session_state.файлы)
                        sleep(3)
                        #
                        # Требуются login и password для входа в JIRA
                        #
                        # try:
                        #     st.session_state.jira = JIRA(
                        #         options={
                        #             "server": "https://jira.data-integration.ru"},
                        #         basic_auth=(
                        #             st.secrets['JIRA']['login'],
                        #             st.secrets['JIRA']['password'])
                        #     )
                        #     description = "ЗАЯВКА\n\n" + st.session_state.текст_заявки
                        #     issue = st.session_state.jira.create_issue(fields={
                        #         "project": {'key': 'JAT'},
                        #         "summary": f"{st.session_state.объект}",
                        #         "description": description,
                        #         "issuetype": {'name': 'Task'},
                        #         "customfield_10310": {"value": "DIS Group"}
                        #     })
                        #     # Прикрепление файлов
                        #     if len(st.session_state.файлы):
                        #         with st.spinner("Отправка файлов", show_time=True):
                        #             for _ in st.session_state.файлы:
                        #                 st.session_state.jira.add_attachment(
                        #                     issue=issue.key,
                        #                     attachment=BytesIO(_.getvalue()),
                        #                     filename=_.name
                        #                 )
                        #     st.success("Заявка отправлена!")
                        #     sleep(3)
                        # except:
                        #     st.error("ОШИБКА! Обратитесь к администратору!")
                        #     sleep(3)
                st.rerun()
    elif st.session_state.заявка_отправлена:
        st.success("Ваша заявка отправлена!")
        if st.button("Новая заявка"):
            st.session_state.заявка_отправлена = False
            st.session_state.заявка = False
            st.rerun()
    else:
        if st.button("Новая заявка"):
            st.session_state.заявка_отправлена = False
            st.session_state.заявка = False
            st.rerun()

with st.expander("Код приложения"):
    st.caption("Файл приложения `qr.py`")
    with open("qr.py", 'r', encoding='utf8') as f: t = f.read()
    st.code(t)
    st.caption("Файл настройки приложения `.streamlit/config.toml`")
    with open(".streamlit/config.toml", 'r', encoding='utf8') as f: t = f.read()
    st.code(t, language="toml")
