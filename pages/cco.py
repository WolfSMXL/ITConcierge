import os

import streamlit as st
from jira import JIRA

from files.py.functions import Убрать_streamlit, request, setup_page_config, init_session_state



def main():
    init_session_state()
    try:
        # Настройка страницы
        setup_page_config()
        Убрать_streamlit()

      # Форма заявки
        try:
            request(
                object="Кабинет Косилова"
            )
        except Exception as e:
            st.error(f"Ошибка при создании заявки: {str(e)}")
            st.rerun()

    except Exception as e:
        st.error(f"Ошибка приложения: {str(e)}")
        st.rerun()

if __name__ == "__main__":
    main()