import base64
import os
from pathlib import Path

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from time import sleep, time
from jira.client import JIRA
import psycopg2
import re

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

jira = None

try:
    jira = JIRA(
            options={"server": "https://jira03ika.data-integration.ru/"},
            basic_auth=(
                "maximov_m",
                "A+z2I#oXl$BQkB!v1v+"
            ),
            async_=True
        )
    st.session_state.аутентификация = True
except Exception as e:
    print(str(e))

# Соединение с Jira
if 'jira' not in st.session_state: st.session_state.jira = jira
# Статус заявки
if not 'заявка' in st.session_state: st.session_state.заявка = False
# Счётчик попыток создания заявок в одном сеансе
if not 'счётчик' in st.session_state: st.session_state.счётчик = 0
# Текст заявки
if not 'текст_заявки' in st.session_state:
    st.session_state.текст_заявки = ''
# Статус аутентификации
if not 'аутентификация' in st.session_state:
    st.session_state.аутентификация = False
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
    projects = JIRA.projects(st.session_state.jira)
    admin_help = -1
    business_support = -1
    for i in projects:
        if i.name == "Admin Help":
            admin_help = i.id
        if i.name == "Business Support":
            business_support = i.id

    text_arr = текст.split(":\n")
    split_text = []
    for i in text_arr:
        split_text.append(re.sub(r"\n\d\) ",", ", i).strip("\n"))
    filtered_split_text = list(filter(None,split_text))
    filtered_split_text = "\n\n".join(filtered_split_text)
    filtered_split_text = filtered_split_text.split("\n\n")

    tech, service, improve, other = -1,-1,-1,-1
    try:
        tech = filtered_split_text.index('В техподдержку')
        service = filtered_split_text.index('Обслуживающему персоналу')
        improve = filtered_split_text.index('Предлагается улучшение')
        other = filtered_split_text.index('Другие предложения')

    except ValueError as v:
        print()

    if tech != -1:
        issue_dict = {
            'project': {'id': admin_help},
            'summary': f"Проблема в {st.session_state.объект}",
            'description': filtered_split_text[tech+1].strip(", "),
            'issuetype': 'Задача'
        }
        try:
            JIRA.create_issue(st.session_state.jira,issue_dict)
        except Exception as e:
            print(str(e))

    if service != -1:
        issue_dict = {
            'project': {'id': business_support},
            'summary': f"Проблема в {st.session_state.объект}",
            'description': filtered_split_text[service+1].strip(", "),
            'issuetype': 'Задача'
        }
        try:
            JIRA.create_issue(st.session_state.jira,issue_dict)
        except Exception as e:
            print(str(e))

    if improve != -1:
        issue_dict = {
            'project': {'id': admin_help},
            'summary': f"Предложение по улучшению для {st.session_state.объект}",
            'description': filtered_split_text[improve + 1].strip(", "),
            'issuetype': 'Задача'
        }
        try:
            JIRA.create_issue(st.session_state.jira,issue_dict)
        except Exception as e:
            print(str(e))

    if other != -1:
        issue_list = [
            {
                'project': {'id': admin_help},
                'summary': f"Проблема в {st.session_state.объект}",
                'description': filtered_split_text[other + 1].strip(", "),
                'issuetype': 'Задача'
            },
            {
                'project': {'id': business_support},
                'summary': f"Проблема в {st.session_state.объект}",
                'description': filtered_split_text[other + 1].strip(", "),
                'issuetype': 'Задача'
            }
        ]
        try:
            JIRA.create_issues(st.session_state.jira,issue_list)
        except Exception as e:
            print(str(e))

    st.rerun()


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
    if i != 1:
        st.session_state.текст_заявки += "\n"
    i = 1
    for _ in ПРОБЛЕМЫ["Обслуживание"]:
        if _ in st.session_state.проблемы:
            if i == 1: st.session_state.текст_заявки += "Обслуживающему персоналу:\n\n"
            st.session_state.текст_заявки += str(i) + ") " + _ + "\n"
            i += 1
    if i != 1:
        st.session_state.текст_заявки += "\n"
    i = 1
    if st.session_state.предложить_улучшение:
        st.session_state.текст_заявки += ("Предлагается улучшение:\n\n" +
                                          st.session_state.предложить_улучшение.strip() + "\n\n")
        i += 1
    if st.session_state.другое:
        st.session_state.текст_заявки += "Другие предложения:\n\n" + st.session_state.другое.strip()
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
    # Проверка имени пользователя и пароля
    try:
        test = JIRA(
            options={"server": "http://jira03ika.data-integration.ru/"},
            basic_auth=(
                st.session_state.имя_пользователя,
                st.session_state.пароль_пользователя
            )
        )
        st.session_state.jira = test
        if 'пользователь_информация' not in st.session_state:
            st.session_state.пользователь_информация = \
                st.session_state.jira.myself()
        st.session_state.пользователь = \
            st.session_state.пользователь_информация.get(
                'displayName', "Аноним")
        return True
    except Exception as e:
        #st.error("Отказ в аутентификации пользователя:"+str(e))
        print(str(e))
        #sleep(3)
        return False

# Если пользователь не аутентифицирован, показываем форму входа
if not st.session_state.аутентификация:
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
            test = Аутентификация()
            if test:
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
    st.header(f"Добро пожаловать, {st.session_state.пользователь}!")
    # Обработка выхода
    if st.session_state.logout:
        # Сброс данных сессии
        st.session_state.аутентификация = False
        print(st.session_state.аутентификация)
        cookies['authenticated'] = 'false'
        cookies['username'] = ''
        cookies['expires_at'] = '0'
        cookies.save()

    conn = psycopg2.connect(dbname='testdb', user='admin',
                            password='admin', host='nifi01-cons.data-integration.ru', port='5432')
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
