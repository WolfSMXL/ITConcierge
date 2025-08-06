# files/py/jira_auth.py
from jira import JIRA

def check_jira_auth(username, password):
    """Проверка авторизации в JIRA"""
    try:
        JIRA(
            server="https://jira.data-integration.ru",
            basic_auth=(username, password),
            timeout=10
        )
        return True
    except Exception:
        return False