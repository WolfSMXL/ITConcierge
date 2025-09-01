import base64
import io
import os
from pathlib import Path
from dotenv import load_dotenv
import jira
import requests
import time
from urllib.parse import urlencode
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
from time import sleep, time
from jira.client import JIRA
import psycopg2
import re
import csv
from pathlib import Path
from files.py.functions import cookies, init_session_state

load_dotenv()

base_path = Path(__file__)
objects_file_path = (base_path / "../files/csv/objects.csv").resolve()
service_problems_file_path = (base_path / "../files/csv/problems.csv").resolve()
technical_problems_file_path = (base_path / "../files/csv/problems.csv").resolve()
objects_problems_file_path = (base_path / "../files/csv/problems_objects.csv").resolve()

hide_decoration_bar_style = '''
    <style>
        [data-testid="stDecoration"] {
            display: none;
        }
    </style>
'''
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

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



# # Соединение с Jira
# if 'jira' not in st.session_state:
#     try:
#         token_auth = (os.getenv("TECH_LOGIN"), os.getenv("TECH_PASSWORD"))
#         test = os.getenv("JIRA_SERVER")
#         jira = JIRA(
#             options={"server": os.getenv("JIRA_SERVER")},
#             basic_auth=token_auth
#         )
#     except Exception as e:
#         print(str(e))
#         jira = None
#     st.session_state.jira = jira
# # Статус заявки
# if not 'request' in st.session_state: st.session_state.request = False
# # Счётчик попыток создания заявок в одном сеансе
# if not 'counter' in st.session_state: st.session_state.counter = 0
# # Текст заявки
# if not 'request_body' in st.session_state: st.session_state.request_body = ''
# # Статус аутентификации
# if not 'auth' in st.session_state: st.session_state.auth = False
# # Статус заявки
# if not 'request_sent' in st.session_state: st.session_state.request_sent = False
# # Название проблемного объекта
# if not 'object' in st.session_state: st.session_state.object = st.query_params.get('object', None)
# # Пользователь
# if not 'user' in st.session_state: st.session_state.user = st.query_params.get(
#     'user', "Аноним")
# # Имя пользователя
# if not 'user_name' in st.session_state: st.session_state.user_name = "Аноним"
# # Обработка выхода
# if "other" not in st.session_state: st.session_state.other = None
#
# query_params = st.query_params
# if 'logout' not in query_params.keys():
#     query_params['logout'] = "false"
#
# if query_params['logout'] == "true":
#     st.session_state.logout = True
# else:
#     st.session_state.logout = False

init_session_state()

def create_tasks(body: str, files: list) -> None:
    jira = st.session_state.jira
    projects = jira.projects()
    admin_help = -1
    business_support = -1
    for i in projects:
        if i.key == "AH":
            admin_help = i.id
        if i.key == "BS":
            business_support = i.id

    text_arr = body.split(":\n")
    split_text = []
    for i in text_arr:
        split_text.append(re.sub(r"\n\d\) ",", ", i).strip("\n"))
    filtered_split_text = list(filter(None,split_text))
    filtered_split_text = "\n\n".join(filtered_split_text)
    filtered_split_text = filtered_split_text.split("\n\n")

    tech, service, improve, other = -1,-1,-1,-1
    try:
        for i in range(0,len(filtered_split_text)):
            if filtered_split_text[i] == 'В техподдержку': tech = i
            if filtered_split_text[i] == 'Обслуживающему персоналу': service = i
            if filtered_split_text[i] == 'Другие предложения': other = i

    except ValueError as v:
        print(str(v))

    issues_list = []

    if tech != -1:
        issue_dict = {
            'project': {'id': admin_help},
            'summary': f"Проблема в {st.session_state.object}",
            'description': filtered_split_text[tech+1].strip(", "),
            'issuetype': 'Задача'
        }
        issues_list.append(issue_dict)

    if service != -1:
        issue_dict = {
            'project': {'id': business_support},
            'summary': f"Проблема в {st.session_state.object}",
            'description': filtered_split_text[service+1].strip(", "),
            'issuetype': 'Задача'
        }
        issues_list.append(issue_dict)

    if other != -1:
        issue_dict = {
                'project': {'id': admin_help},
                'summary': f"Другая проблема в {st.session_state.object}",
                'description': filtered_split_text[other + 1].strip(", "),
                'issuetype': 'Задача'
            }
        issues_list.append(issue_dict)

    try:
        issues = jira.create_issues(issues_list)
        if len(files) != 0:
            for i in issues:
                for j in files:
                    bytesio = io.BytesIO(j.getvalue())
                    bytesio.seek(0)
                    jira.add_attachment(issue=i["issue"], attachment=bytesio, filename=j.name)
    except Exception as e:
        if "CAPTCHA_CHALLENGE" in str(e):
            # Логика обработки капчи
            login_url = os.getenv("JIRA_SERVER")+'login.jsp'
            params = {'continue': '/rest/api/2/serverInfo'}
            redirect_url = f"{login_url}?{urlencode(params)}"
            st.write(f"Необходимо ввести капчу. Откройте следующую ссылку и следуйте инструкциям:")
            st.write(redirect_url)
            if st.button("Подтвердить ввод капчи"):
                st.rerun()
        else:
            print(f"Ошибка при создании заявки: {str(e)}")

    st.rerun()


def check_object() -> bool:
    """Процедура проверяет - выбран проблемный объект или нет.
    Возвращает `True` если выбран. Иначе - `False`"""
    try:
        if st.session_state.object: return True
    except:
        st.empty()
        return False


def build_request() -> None:
    """Процедура собирает текст заявки из полей формы"""
    st.session_state.request_body = ""
    i = 1
    for _ in problems_dict["Техподдержка"]:
        if _ in st.session_state.technical_problems:
            if i == 1: st.session_state.request_body += "В техподдержку:\n\n"
            st.session_state.request_body += str(i) + ") " + _ + "\n"
            i += 1
    if i != 1:
        st.session_state.request_body += "\n"
    i = 1
    for _ in problems_dict["Обслуживание"]:
        if _ in st.session_state.service_problems:
            if i == 1: st.session_state.request_body += "Обслуживающему персоналу:\n\n"
            st.session_state.request_body += str(i) + ") " + _ + "\n"
            i += 1
    if i != 1:
        st.session_state.request_body += "\n"
    i = 1
    if st.session_state.other:
        st.session_state.request_body += "Другие предложения:\n\n" + st.session_state.other.strip()
    return None


def check_fields() -> bool:
    """Процедура проверяет заполнение полей заявки и возвращает `True`,
    если поля заполнялись. В ином случае возвращает `False`"""
    if st.session_state.request_body or len(st.session_state.файлы):
        return True
    else:
        return False


def checks() -> None:
    """Процедура выполняет проверки заполнения полей формы, выбора
    проблемных объектов и сведений о пользователе. В тех случаях, когда
    отсутствуют исходные данные (наименование проблемного объекта,
    отсутствуют какие-либо сведения о проблемах и не приложен ни один
    файл) процедура переводит значение статуса заявки в состояние False
    """
    # Проверка выбора объекта
    if check_object():
        st.info("Проблемный объект: " + st.session_state.object)
        sleep(3)
        st.session_state.request = True
    else:
        st.warning("Необходимо выбрать проблемный объект!")
        sleep(3)
        st.session_state.request = False
    # Проверка заполнения полей заявки
    if (not st.session_state.request_body == "") or \
            (not len(st.session_state.файлы)):
        if st.session_state.request_body:
            st.info("Текст заявки: \n" + st.session_state.request_body)
        if len(st.session_state.файлы):
            st.info("Добавлено файлов: " + \
                    str(len(st.session_state.файлы)))
        sleep(3)
        st.session_state.request = True
    else:
        st.warning("Необходимо заполнить поля заявки!")
        sleep(3)
        st.session_state.request = False
    return None

def auto_login():
    # Пробуем достать логин из куки
    stored_username = cookies.get('username', '')
    if stored_username:
        st.session_state.auth = True
        st.session_state.user_name = stored_username
        return True
    return False

auto_logged_in = auto_login()


# @st.cache_data
# def authentication() -> bool:
#     """Процедура аутентификации пользователя в Jira.
#     При нахождении пользователя в системе возвращает True.
#     В обратном случае возвращает False"""
#     # Проверка имени пользователя и пароля
#     try:
#         token_auth = (os.getenv("TECH_LOGIN"), os.getenv("TECH_PASSWORD"))
#         st.session_state.jira = JIRA(
#             options={"server": os.getenv("JIRA_SERVER")},
#             token_auth=token_auth,
#             async_=True,
#             max_retries=2
#         )
#
#         st.session_state.auth = True
#         if 'user_info' not in st.session_state:
#             st.session_state.user_info = \
#                 st.session_state.jira.myself()
#         st.session_state.user = \
#             st.session_state.user_info.get(
#                 'displayName', "Аноним")
#         return True
#     except Exception as e:
#         print(str(e))
#         return False


# Если пользователь не аутентифицирован, показываем форму входа

if not st.session_state.auth and not auto_logged_in:
    st.empty()
    c1, c2, c3 = st.columns([1, 4, 1])
    with c2.form("auth_form"):
        #st.image("files/png/Jira.webp", use_container_width=True)
        st.session_state.user_name = st.text_input("Имя")
        remember_me = st.checkbox("Запомнить", value=True)
        submit_button = st.form_submit_button(
            "Вход", use_container_width=True)
        if submit_button:
                st.session_state.auth = True
                if remember_me:
                    # Устанавливаем cookie с сроком действия 30 дней
                    cookies['authenticated'] = 'true'
                    cookies['username'] = st.session_state.user_name
                    expires_at = int(time()) + 30 * 24 * 60 * 60  # 30 дней
                    cookies['expires_at'] = str(expires_at)
                    cookies.save()
                    # Обновляем страницу, чтобы скрыть форму входа
                st.rerun()

# Если пользователь ёцирован, показываем основное содержимое
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
            <button>Выйти</button>
        </form>
    </div>
    """, unsafe_allow_html=True)

    saved_username = cookies.get('username', '')
    if saved_username:
        st.session_state.user_name = saved_username

    # if cookies["authenticated"] == 'true':
    #     user_login = JIRA.user(st.session_state.jira, cookies["username"])
    # elif st.session_state.user_name:
    #     user_login = JIRA.user(st.session_state.jira, st.session_state.user_name)
    # else:
    #     st.error("Пользователь не авторизован")

    user_login = JIRA.user(st.session_state.jira, st.session_state.user_name).displayName
    st.header(f"Добро пожаловать, {user_login}!")
    # Обработка выхода
    if st.session_state.logout:
        # Сброс данных сессии
        st.session_state.auth = False
        cookies['authenticated'] = 'false'
        cookies['username'] = ''
        cookies['expires_at'] = '0'
        cookies.save()
        st.query_params.pop("logout")
        st.rerun()

    objects = []
    object_categories = []
    with objects_file_path.open(encoding="utf-8") as f:
        objects_csv = csv.reader(f)
        next(objects_csv)
        for i in objects_csv:
            objects.append(i[0])
            object_categories.append(i[1])


    service_problems = []
    with service_problems_file_path.open(encoding="utf-8") as f:
        service_problems_csv = csv.reader(f)
        next(service_problems_csv)
        for i in service_problems_csv:
            if i[0] == "Обслуживание":
                service_problems.append(i[1])


    technical_problems = []
    with technical_problems_file_path.open(encoding="utf-8") as f:
        technical_problems_csv = csv.reader(f)
        next(technical_problems_csv)
        for i in technical_problems_csv:
            if i[0] == "Техническая":
                technical_problems.append(i[1])

    problems_dict = dict()
    problems_dict["Техподдержка"] = technical_problems
    problems_dict["Обслуживание"] = service_problems

    if (not st.session_state.request_sent) and (not st.session_state.request):
        st.divider()
        object_category = st.selectbox("Выберите категорию объекта", options=set(object_categories))

        objects_by_category = []

        with objects_file_path.open(encoding="utf-8") as f:
            objects_csv = csv.reader(f)
            next(objects_csv)
            for i in objects_csv:
                if i[1] == object_category:
                    objects_by_category.append(i[0])

        st.session_state.object = st.selectbox("Выберите объект", options=objects_by_category)

        st.write("Причина обращения")

        chosen_object = None

        with objects_problems_file_path.open(encoding="utf-8") as f:
            objects_problems_csv = csv.reader(f)
            next(objects_problems_csv)
            for i in objects_problems_csv:
                if i[0] == st.session_state.object:
                    chosen_object = i
                    break
            else:
                st.error("Не найдено помещение в файле objects_problems.csv")

        if len(chosen_object) != 0:
            tech_obj_prob = list()
            serv_obj_prob = list()

            for i in chosen_object[1].split(";"):
                if i in technical_problems:
                    tech_obj_prob.append(i)
                if i in service_problems:
                    serv_obj_prob.append(i)

            left, right = st.columns([1, 1])
            tech_chosen_problems = left.pills("Техническая", key='technical_problems',
                                          options=tech_obj_prob + ["Другое"],
                                          selection_mode="multi")

            serv_chosen_problems = right.pills("Сервисная", key='service_problems',
                                        options=serv_obj_prob,
                                        selection_mode="multi")

            if "Другое" in tech_chosen_problems or "Другое" in serv_chosen_problems:
                st.text_area("Другое", key="other")

        st.file_uploader("Добавить вложение",
                         key="файлы",
                         type=["jpg", "jpeg", "png", "pdf", "doc",
                               "docx", "xls", "xlsx"],
                         accept_multiple_files=True)

        if st.button("Отправить заявку"):
            build_request()
            if not check_object():
                st.error("Не выбран объект!")
                sleep(1)
            else:
                if not check_fields():
                    st.error("Форма не заполнена!")
                    sleep(1)
                else:
                    st.info("Проверки выполнены...")
                    st.info(st.session_state.request_body)
                    st.info("Приложенных файлов: " + \
                            str(len(st.session_state.файлы)))
                    create_tasks(st.session_state.request_body, st.session_state.файлы)
                    sleep(3)
            st.rerun()
        st.divider()
    elif st.session_state.request_sent:
        st.success("Ваша заявка отправлена!")
        if st.button("Новая заявка"):
            st.session_state.request_sent = False
            st.session_state.request = False
            st.rerun()
    else:
        if st.button("Новая заявка"):
            st.session_state.request_sent = False
            st.session_state.request = False
            st.rerun()
