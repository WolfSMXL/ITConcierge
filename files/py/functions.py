import streamlit as st
import time
from io import BytesIO
from files.py.auth import init_auth

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

def exit(auth_manager):
        if st.session_state.auth['authenticated']:
            _, col = st.columns([8, 1])
            with col:
                if st.button("Выход", type="secondary", key="logout_button_main"):
                    auth_manager.clear_auth()
                    st.rerun()

def Заказ(помещение: str, загружать_файлы: bool = True):
    """Форма создания заявки с st.pills и множественным выбором"""
    # Добавляем CSS для стилизации только кнопки отправки
    st.markdown("""
    <style>
        /* Стили только для кнопки отправки заявки */
        div[data-testid="stButton"] button[kind="primary"] {
            border: none !important;
            box-shadow: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # if "auth" not in st.session_state or not st.session_state.auth.get("authenticated"):
    #     st.error("Требуется авторизация")
    #     return
    
    # try:
    #     jira = st.session_state.auth["jira_conn"]
    #     jira.myself()
    # except Exception as e:
    #     st.error(f"Ошибка соединения с JIRA: {str(e)}")
    #     st.session_state.auth["authenticated"] = False
    #     st.rerun()
    #     return
    
    # Ключи для состояния
    PILLS_KEY = f"pills_state_{помещение}"
    
    # Инициализация состояния
    if PILLS_KEY not in st.session_state:
        st.session_state[PILLS_KEY] = []
    
    # Обработка успешной отправки
    if "success_message" in st.session_state:
        st.success(f"Заявка {st.session_state.success_message} успешно создана!")
        del st.session_state.success_message
        time.sleep(7)
        st.rerun()

    # Основной контейнер
    with st.container():
        # Выбор проблем через pills
        current_selection = st.pills(
            "Выбрать проблемы",
            options=[
                "Проблема с оборудованием",
                "Не работает ВКС",
                "Интернет сбой",
                "Предложить улучшение",
                "Другое"
            ],
            selection_mode="multi",
            default=st.session_state[PILLS_KEY],
            key=f"problems_pills_{помещение}"
        )
        
        # Обновляем состояние при изменении выбора
        if current_selection != st.session_state[PILLS_KEY]:
            st.session_state[PILLS_KEY] = current_selection
            st.rerun()

        # Определяем, нужно ли показывать дополнительные сведения
        show_additional = any(item in current_selection for item in ["Другое", "Предложить улучшение"])
        
        # Дополнительные сведения
        additional_info = ""
        if show_additional:
            additional_info = st.text_area(
                "Дополнительные сведения*",
                value="",
                height=100,
                key=f"additional_{помещение}"
            )

        # Загрузка файлов
        uploaded_files = []
        if загружать_файлы:
            uploaded_files = st.file_uploader(
                "Прикрепить файлы",
                type=["jpg", "jpeg", "png", "pdf", "doc", "docx", "xls", "xlsx"],
                accept_multiple_files=True,
                key=f"file_uploader_{помещение}"
            )
            if uploaded_files:
                st.caption(f"Выбрано файлов: {len(uploaded_files)}")

        # Кнопка отправки (без формы)
        submitted = st.button("Отправить заявку", 
                            type="primary", 
                            key=f"submit_{помещение}")
        
        if submitted:
            # Валидация
            if not current_selection and not additional_info and not uploaded_files:
                st.error("Пожалуйста, укажите проблему, дополнительные сведения или прикрепите файлы")
                st.stop()
                
            if show_additional and not additional_info.strip():
                st.error("Для выбранных пунктов требуются дополнительные сведения")
                st.stop()

            # Формирование заявки
            try:
                description = "ЗАЯВКА\n\n" + "\n".join(f"• {p}" for p in current_selection)
                if additional_info.strip():
                    description += f"\n\nДополнительно:\n{additional_info}"

                issue = st.session_state.jira.create_issue(fields={
                    "project": {'key': 'JAT'},
                    "summary": f"{помещение}",
                    "description": description,
                    "issuetype": {'name': 'Task'},
                    "customfield_10310": {"value": "DIS Group"}
                })

                # Прикрепление файлов
                if uploaded_files:
                    with st.spinner("Отправка файлов"):
                        for file in uploaded_files:
                            st.session_state.jira.add_attachment(
                                issue=issue.key, 
                                attachment=BytesIO(file.getvalue()), 
                                filename=file.name
                            )

                # Устанавливаем флаг успешной отправки
                st.session_state.success_message = issue.key
                st.session_state[PILLS_KEY] = []  # Сбрасываем выбор проблем
                st.rerun()

            except Exception as e:
                st.error(f"Ошибка: {str(e)}")