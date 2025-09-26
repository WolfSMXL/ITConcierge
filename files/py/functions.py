import base64
import csv
import io
import os
import re
from email.message import EmailMessage
from pathlib import Path
from time import sleep, time
from urllib.parse import urlencode
from random import randint

import streamlit as st
from exchangelib import DELEGATE, Account, Credentials, Message, Mailbox, HTMLBody
from jira import JIRA
from streamlit_cookies_manager import EncryptedCookieManager


def hide_sidebar():
    """Скрывает боковую панель полностью, включая стрелку для её отображения."""
    st.markdown("""
    <style>
        /* Скрыть главную боковую панель */
        [data-testid="stSidebar"] {
            display: none !important;
        }

        /* Скрыть область навигационной стрелки (включая кнопку) */
        body > div > div:nth-child(1) > div:nth-child(1) > div > div > div > div:nth-child(2) > button {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def setup_page_config():
    hide_decoration_bar_style = '''
        <style>
            [data-testid="stDecoration"] {
                display: none;
            }
        </style>
    '''
    st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

    st.markdown(
        '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">',
        unsafe_allow_html=True)
    img = Path(__file__).parent.parent / "png/DISg_colored.png"
    img_bytes = img.read_bytes()
    encoded_img = base64.b64encode(img_bytes).decode()
    img_html = "data:image/png;base64,{}".format(encoded_img)
    st.markdown(f"""
    <nav class="navbar fixed-top navbar-expand-lg navbar-dark">
      <a href="https://www.dis-group.ru">
        <img src="{img_html}" width=30 class="navbar-brand" target="_blank"></img>
      </a>
    </nav>
    """, unsafe_allow_html=True)

    st.set_page_config(
        page_title="Admin, Help!",
        page_icon="files/ico/DISg_colored.ico",
        layout="centered",
        initial_sidebar_state="collapsed"
    )

def Убрать_streamlit(флаг: bool = True):
    """Скрывает элементы интерфейса Streamlit"""
    if флаг:
        st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)

def Вход(auth_manager):
    """Форма входа в систему"""
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input("Имя пользователя", key="login_username_input")
        password = st.text_input("Пароль", type="password", key="login_password_input")
        
        if st.form_submit_button("Войти"):
            if auth_manager.save_auth(username, password):
                st.session_state.login_attempt = True
                st.rerun()
            else:
                st.error("Неверные учетные данные")

def send_email():
    base_path = Path(__file__).parent
    connections_file_path = (base_path / "../csv/printer_connections.csv").resolve()
    connection_link = ""
    with connections_file_path.open(encoding="utf-8") as f:
        connections_csv = csv.reader(f)
        next(connections_csv)
        for i in connections_csv:
            if i[0] == st.session_state.object:
                connection_link = i[1]

    credentials = Credentials(
        username=os.getenv("OUTLOOK_TECH_LOGIN"),
        password=os.getenv("OUTLOOK_TECH_PASSWORD")
    )
    a = Account(
        primary_smtp_address=os.getenv("OUTLOOK_TECH_LOGIN"),
        credentials=credentials,
        autodiscover=True,
        access_type=DELEGATE
    )

    email = EmailMessage()
    email["From"] = os.getenv("OUTLOOK_TECH_LOGIN")
    email["To"] = st.session_state.user_email
    email["Subject"] = "Инструкция по подключению принтера"

    email_body = f"""<pre>
    Для самостоятельного подключения «{st.session_state.object}» перейти по ссылке <a href="{connection_link}">{connection_link}</a>
    Подробную инструкцию можно посмотреть на <a href="https://mayak.data-integration.ru/kms/CM/INTERNAL/LAYOUT?item_id=20430&homePage=%2FCM%2FT_PIVOT_DOCS_ICS%2FVIEW%3Fitem_id%3D30701&homePageEncoded=true">Маяке</a>
    Если что-то пошло не так, приходи к нам в техническую поддержку:
    <a href="https://jira.data-integration.ru/plugins/servlet/desk/portal/1">Портал Admin Help</a>
    </pre>"""

    m = Message(
        account=a,
        subject="Инструкция по подключению принтера",
        body=HTMLBody(email_body),
        to_recipients=[
            Mailbox(email_address=st.session_state.user_email)
        ]
    )
    m.send()

def send_code_email():
    credentials = Credentials(
        username=os.getenv("OUTLOOK_TECH_LOGIN"),
        password=os.getenv("OUTLOOK_TECH_PASSWORD")
    )
    a = Account(
        primary_smtp_address=os.getenv("OUTLOOK_TECH_LOGIN"),
        credentials=credentials,
        autodiscover=True,
        access_type=DELEGATE
    )

    email = EmailMessage()
    email["From"] = os.getenv("OUTLOOK_TECH_LOGIN")
    email["To"] = st.session_state.user_email
    email["Subject"] = "Код подтверждения для входа в Консьерж"

    email_body = f"""<pre>
        Код подтверждения: {st.session_state.code}
        </pre>"""

    m = Message(
        account=a,
        subject="Код подтверждения для входа в Консьерж",
        body=HTMLBody(email_body),
        to_recipients=[
            Mailbox(email_address=st.session_state.user_email)
        ]
    )
    m.send()

def exit(auth_manager):
        if st.session_state.auth['authenticated']:
            _, col = st.columns([8, 1])
            with col:
                if st.button("Выход", type="secondary", key="logout_button_main"):
                    auth_manager.clear_auth()
                    st.rerun()

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
        if st.session_state.other_it:
            issue_dict = {
                'project': {'id': admin_help},
                'summary': f"Другая проблема в {st.session_state.object}",
                'description': filtered_split_text[other + 1].strip(", "),
                'issuetype': 'Задача'
            }
            issues_list.append(issue_dict)
        if st.session_state.other_serv:
            issue_dict = {
                    'project': {'id': business_support},
                    'summary': f"Другая проблема в {st.session_state.object}",
                    'description': filtered_split_text[other + 1].strip(", "),
                    'issuetype': 'Задача'
                }
            issues_list.append(issue_dict)


    try:
        issues = jira.create_issues(issues_list)
        if not st.session_state.anonymous:
            for i in issues:
                i["issue"].update(reporter={'name': st.session_state.user.name})
        if len(files) != 0:
            for i in issues:
                for j in files:
                    bytesio = io.BytesIO(j.getvalue())
                    bytesio.seek(0)
                    jira.add_attachment(issue=i["issue"], attachment=bytesio, filename=j.name)

        if not st.session_state.anonymous and st.session_state.printer_connect:
            send_email()
        request_info(issues)
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

def build_request(problems_dict) -> None:
    """Процедура собирает текст заявки из полей формы"""
    st.session_state.request_body = ""
    i = 1
    if "technical_problems" in st.session_state:
        for _ in problems_dict["Техподдержка"]:
            if _ in st.session_state.technical_problems:
                if i == 1: st.session_state.request_body += "В техподдержку:\n\n"
                line_end = ""
                if _ == "Проблемы с оборудованием":
                    if "equipment" in st.session_state or "other_equipment" in st.session_state:
                        line_end += " ("
                        if "equipment" in st.session_state:
                            for j in st.session_state.equipment:
                                line_end += j + ", "
                        if "other_equipment" in st.session_state:
                            for j in st.session_state.other_equipment:
                                line_end += j
                        line_end = line_end.rstrip(", ")
                        line_end += ")"

                line_end += "\n"
                st.session_state.request_body += str(i) + ") " + _ + line_end
                i += 1
    if i != 1:
        st.session_state.request_body += "\n"
    i = 1
    if "service_problems" in st.session_state:
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

def check_object() -> bool:
    """Процедура проверяет - выбран проблемный объект или нет.
    Возвращает `True` если выбран. Иначе - `False`"""
    try:
        if st.session_state.object: return True
    except:
        st.empty()
        return False

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

def init_session_state():
    # Соединение с Jira
    if 'jira' not in st.session_state:
        try:
            basic_auth = (os.getenv("JIRA_TECH_LOGIN"), os.getenv("JIRA_TECH_PASSWORD"))
            jira = JIRA(
                options={"server": os.getenv("JIRA_SERVER")},
                basic_auth=basic_auth
            )
        except Exception as e:
            print(str(e))
            jira = None
        if jira:
            st.session_state.jira = jira
        else:
            st.error("Не удалось подключиться к JIRA")
    # Статус заявки
    if not 'request' in st.session_state: st.session_state.request = False
    # Счётчик попыток создания заявок в одном сеансе
    if not 'counter' in st.session_state: st.session_state.counter = 0
    # Текст заявки
    if not 'request_body' in st.session_state: st.session_state.request_body = ''
    # Статус аутентификации
    if not 'auth' in st.session_state: st.session_state.auth = False
    # Статус заявки
    if not 'request_sent' in st.session_state: st.session_state.request_sent = False
    # Название проблемного объекта
    if not 'object' in st.session_state: st.session_state.object = st.query_params.get('object', None)
    # Пользователь
    if not 'user' in st.session_state: st.session_state.user = st.query_params.get(
        'user', "Аноним")
    # Имя пользователя
    if not 'user_name' in st.session_state: st.session_state.user_email = "Аноним"
    # Обработка выхода
    if "other" not in st.session_state: st.session_state.other = None
    if "cookies" not in st.session_state:
        init_cookies()
    query_params = st.query_params
    if 'logout' not in query_params.keys():
        query_params['logout'] = "false"
    if query_params['logout'] == "true":
        st.session_state.logout = True
    else:
        st.session_state.logout = False
    if "code" not in st.session_state:
        st.session_state.code = 0

def init_cookies():
    # Создание экземпляра менеджера куков
    cookies = EncryptedCookieManager(
        prefix=st.secrets["Крошки"]["префикс"],
        password=os.environ.get("COOKIES_PASSWORD", st.secrets["Крошки"]["пароль"])
    )

    if not cookies.ready():
        st.spinner("Ожидание загрузки хлебных крошек", show_time=True)
        st.stop()

    st.session_state.cookies = cookies

def auto_login():
    sleep(0.5)
    cookies = st.session_state.cookies
    # Пробуем достать логин из куки
    stored_username = cookies.get('username', '')
    if stored_username:
        st.session_state.auth = True
        st.session_state.user_email = stored_username
        return True
    return False

@st.dialog("Информация", on_dismiss="rerun")
def request_info(issues):
    issues_text = ""
    for i in issues:
        issues_text += f"[{str(i['issue'].key)}]({os.getenv('JIRA_SERVER').rstrip(r"/")}/browse/{i['issue']}), "
    st.write(f"Заявка ({issues_text.rstrip(", ")}) успешно создана! Уведомления о статусе заявки буду приходить на почту.")
    if st.session_state.printer_connect and not st.session_state.anonymous:
        st.write("Инструкция по подключению принтера была отправлена на почту")
    if st.button("OK"):
        st.rerun()

@st.dialog("Код подтверждения")
def confirmation():
    cookies = st.session_state.cookies
    st.write("Код подтверждения был отправлен на вашу почту.")
    code = st.text_input("Введите код подтверждения из письма:")
    if st.button("OK"):
        if str(st.session_state.code) == code:
            st.session_state.auth = True
            if st.session_state.remember_me:
                # Устанавливаем cookie с сроком действия 30 дней
                cookies['authenticated'] = 'true'
                cookies['username'] = st.session_state.user_email
                expires_at = int(time()) + 30 * 24 * 60 * 60  # 30 дней
                cookies['expires_at'] = str(expires_at)
                cookies.save()
                st.session_state.cookies = cookies
                # Обновляем страницу, чтобы скрыть форму входа
            st.rerun()
        else:
            st.error("Неверный код")

def request(object: str):
    cookies = st.session_state.cookies
    auto_logged_in = auto_login()
    # Если пользователь не аутентифицирован, показываем форму входа
    if not st.session_state.auth and not auto_logged_in:
        st.empty()
        st.markdown("<h3 style='text-align: center;'>Добро пожаловать в Консьерж сервис!</h3>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 4, 1])
        with c2.form("auth_form"):
            # st.image("files/png/Jira.webp", use_container_width=True)
            st.write("Для авторизации введите вашу электронную почту:")
            st.session_state.user_email = st.text_input("Почта", label_visibility="collapsed")
            st.session_state.remember_me = st.checkbox("Запомнить", value=True)
            submit_button = st.form_submit_button(
                "Вход", use_container_width=True)
            if submit_button:
                st.session_state.code = randint(10000,99999)
                send_code_email()
                confirmation()

    else:
        """Форма создания заявки с st.pills и множественным выбором"""
        base_path = Path(__file__).parent
        objects_file_path = (base_path / "../csv/objects.csv").resolve()
        service_problems_file_path = (base_path / "../csv/problems.csv").resolve()
        technical_problems_file_path = (base_path / "../csv/problems.csv").resolve()
        objects_problems_file_path = (base_path / "../csv/problems_objects.csv").resolve()

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
            st.session_state.user_email = saved_username

        try:
            is_email = False
            split_email_one = st.session_state.user_email.split("@")
            if len(split_email_one) == 2:
                split_email_two = split_email_one[1].split(".")
                if len(split_email_two) == 2:
                    is_email = True

            if is_email:
                user_login = JIRA.search_users(st.session_state.jira, st.session_state.user_email)[0]
                display_name = user_login.displayName
                st.session_state.user = user_login
                st.session_state.anonymous = False
            else:
                raise Exception("Указан неправильный email")
        except Exception as e:
            display_name = "Аноним"
            st.session_state.anonymous = True
        st.header(f"Добро пожаловать, {display_name}!")
        # Обработка выхода
        if st.session_state.logout:
            # Сброс данных сессии
            st.session_state.auth = False
            cookies['authenticated'] = 'false'
            cookies['username'] = ''
            cookies['expires_at'] = '0'
            cookies.save()
            st.session_state.cookies = cookies
            st.query_params["logout"] = "false"
            st.switch_page("qr.py")

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

            if object != "":
                st.session_state.object = object
                st.subheader(st.session_state.object, divider=True)

                with objects_file_path.open(encoding="utf-8") as f:
                    objects_csv = csv.reader(f)
                    next(objects_csv)
                    for i in objects_csv:
                        if i[0] == object:
                            object_category = i[1]
            else:
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

                left, right = None, None

                tech_chosen_problems, serv_chosen_problems = [], []

                if len(tech_obj_prob) != 0 and len(serv_obj_prob) != 0:
                    left, right = st.columns([1, 1])
                elif len(tech_obj_prob) == 0 and len(serv_obj_prob) != 0:
                    right = st
                elif len(tech_obj_prob) != 0 and len(serv_obj_prob) == 0:
                    left = st

                if left is not None:
                    tech_chosen_problems = left.pills("Техническая", key='technical_problems',
                                                  options=tech_obj_prob + ["Другой запрос в ИТ"],
                                                  selection_mode="multi")
                if right is not None:
                    serv_chosen_problems = right.pills("Хозяйственная", key='service_problems',
                                                   options=serv_obj_prob + ["Другой запрос в АХО"],
                                                   selection_mode="multi")

                if "Проблемы с оборудованием" in tech_chosen_problems:
                    if object_category == "Переговорные":
                        equipment_negotiation_list = ["Спикерфон", "Клавиатура/Мышь", "Телевизор", "Ноутбук/Неттоп"]
                        st.pills("Оборудование", key="equipment", options=equipment_negotiation_list,
                                 selection_mode="multi")
                    if object_category == "Кабинеты":
                        equipment_negotiation_list = ["Ноутбук", "Клавиатура/Мышь", "Док-станция", "Монитор", "Телевизор"]
                        st.pills("Оборудование", key="equipment", options=equipment_negotiation_list,
                                 selection_mode="multi")

                left_text, right_text = None, None

                if "Проблемы с оборудованием" in tech_chosen_problems:
                    left_text = st

                if "Другой запрос в ИТ" in tech_chosen_problems or "Другой запрос в АХО" in serv_chosen_problems:
                    if "Проблемы с оборудованием" in tech_chosen_problems:
                        left_text, right_text = st.columns([1, 1])
                    else:
                        right_text = st


                if left_text is not None:
                    left_text.text_area("Другое оборудование", key="other_equipment", placeholder="Другое оборудование", label_visibility="collapsed")
                if right_text is not None:
                    right_text.text_area("Другая причина обращения", key="other", placeholder="Другая причина обращения", label_visibility="collapsed")

                if "Другой запрос в ИТ" in tech_chosen_problems:
                    st.session_state.other_it = True
                else:
                    st.session_state.other_it = False
                if "Другой запрос в АХО" in serv_chosen_problems:
                    st.session_state.other_serv = True
                else:
                    st.session_state.other_serv = False

                if "Подключиться к принтеру" in tech_chosen_problems:
                    st.session_state.printer_connect = True
                else:
                    st.session_state.printer_connect = False




            st.file_uploader("Добавить вложение",
                             key="файлы",
                             type=["jpg", "jpeg", "png", "pdf", "doc",
                                   "docx", "xls", "xlsx"],
                             accept_multiple_files=True)

            hide_label = """
                    <style>
                                [data-testid='stFileUploaderDropzoneInstructions'] > div > span {
                    display: none;
                    }
                                [data-testid='stFileUploaderDropzoneInstructions'] > div::before {
                    content: 'Приложите фото';
                    }
            
                     </style>
                     """
            st.markdown(hide_label, unsafe_allow_html=True)

            if st.button("Отправить заявку"):

                build_request(problems_dict)
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