import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import hashlib
import time

# Инициализация менеджера куки
cookies = EncryptedCookieManager(
    prefix="my_app_",
    password="your_super_secret_password_here")  # Замените на свой надежный пароль

if not cookies.ready():
    # Ждем, пока куки загрузятся
    st.stop()

# Функция для хеширования паролей
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# "База данных" пользователей (в реальном приложении используйте настоящую БД)
users_db = {
    "admin": {
        "password_hash": hash_password("admin123"),
        "name": "Администратор",
        "role": "admin"
    },
    "user1": {
        "password_hash": hash_password("user123"),
        "name": "Обычный пользователь",
        "role": "user"
    }
}

# Функция аутентификации
def authenticate(username, password):
    if username in users_db:
        hashed_password = hash_password(password)
        if users_db[username]["password_hash"] == hashed_password:
            return True
    return False

# Проверка, авторизован ли пользователь
def is_authenticated():
    return cookies.get("authenticated") == "true"

# Функция входа в систему
def login(username):
    cookies["authenticated"] = "true"
    cookies["username"] = username
    cookies["name"] = users_db[username]["name"]
    cookies["role"] = users_db[username]["role"]
    cookies["login_time"] = str(time.time())
    cookies.save()

# Функция выхода из системы
def logout():
    cookies["authenticated"] = "false"
    cookies["username"] = ""
    cookies["name"] = ""
    cookies["role"] = ""
    cookies["login_time"] = ""
    cookies.save()

# Интерфейс аутентификации
def auth_ui():
    st.title("Аутентификация")

    with st.form("auth_form"):
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        submit_button = st.form_submit_button("Войти")

        if submit_button:
            if authenticate(username, password):
                login(username)
                st.success("Успешный вход!")
                st.rerun()
            else:
                st.error("Неверное имя пользователя или пароль")

# Основное приложение
def main_app():
    st.title(f"Добро пожаловать, {cookies.get('name')}!")
    st.write(f"Вы вошли как: {cookies.get('role')}")
    
    if st.button("Выйти"):
        logout()
        st.rerun()
    
    st.write("Здесь может быть ваш защищенный контент...")

# Основная логика приложения
if is_authenticated():
    main_app()
else:
    auth_ui()