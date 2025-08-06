# files/py/cookie_manager.py
from extra_streamlit_components import CookieManager

class CookieManagerWrapper:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.manager = CookieManager(key="unique_cookie_manager_key")
        return cls._instance

def get_cookie_manager():
    return CookieManagerWrapper()