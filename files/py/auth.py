from extra_streamlit_components import CookieManager
from jira import JIRA
import streamlit as st
import uuid
from datetime import datetime

class AuthManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.cookie_manager = CookieManager(key=f"cookie_{uuid.uuid4().hex[:6]}")
        self._ensure_auth_initialized()
    
    def _ensure_auth_initialized(self):
        """Гарантирует инициализацию session_state.auth"""
        if 'auth' not in st.session_state:
            st.session_state.auth = {
                'authenticated': False,
                'username': None,
                'full_name': None,
                'jira_conn': None
            }
    
    def check_auth(self):
        username = st.session_state.username
        print("Логин: " + st.session_state.username)
        self._ensure_auth_initialized()
        if st.session_state.auth['authenticated']:
            return True
        else:
            try:
                cookies = self.cookie_manager.get_all()
                username = cookies.get('app_username')
                print("Куки: " + cookies.get('app_username'))
                print("Логин: " + st.session_state.username)
                password = cookies.get('app_password')
                print("Пароль: " + st.session_state.password)
                if username and password:
                    return self._authenticate(st.session_state.username, st.session_state.password)
            except Exception:
                print("ОШИБКА!")
                return False
    
    def _authenticate(self, username, password):
        try:
            jira = JIRA(
                server="https://jira.data-integration.ru",
                basic_auth=(username, password),
                timeout=10
            )
            user_info = jira.myself()
            
            st.session_state.auth.update({
                'authenticated': True,
                'username': username,
                'full_name': user_info.get('displayName', username),
                'jira_conn': jira
            })
            return True
        except Exception:
            return False
    
    def save_auth(self, username, password):
        if self._authenticate(username, password):
            self.cookie_manager.set('app_username', username)
            self.cookie_manager.set('app_password', password)
            return True
        return False
    
    def clear_auth(self):
        try:
            self.cookie_manager.delete('app_username')
            self.cookie_manager.delete('app_password')
        except Exception:
            pass
            
        self._ensure_auth_initialized()
        st.session_state.auth.update({
            'authenticated': False,
            'username': None,
            'full_name': None,
            'jira_conn': None
        })

def init_auth():
    return AuthManager()