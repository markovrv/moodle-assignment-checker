import requests
from bs4 import BeautifulSoup
from getpass import getpass

# Настройка сессии
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_credentials():
    """Запрашивает логин, пароль и ID курса у пользователя."""
    print("Введите данные для входа в Moodle:")
    username = input("Логин: ").strip()
    password = getpass("Пароль: ").strip()
    course_id = input("ID курса (из URL, например, 28432): ").strip()
    return username, password, course_id

def get_logintoken(login_url):
    """Получает logintoken со страницы входа."""
    response = session.get(login_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    token_input = soup.find("input", {"name": "logintoken"})
    return token_input["value"] if token_input else ""

def login_to_moodle(login_url, username, password):
    """Авторизуется в Moodle."""
    logintoken = get_logintoken(login_url)
    login_data = {
        "anchor": "",
        "logintoken": logintoken,
        "username": username,
        "password": password,
        "rememberusername": "1"
    }
    session.post(login_url, data=login_data, headers=headers)

def extract_assignments(course_url):
    """Собирает ссылки на задания со страницы курса."""
    response = session.get(course_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    return [
        {"name": a.text.strip(), "url": a["href"]}
        for a in soup.find_all("a", class_="aalink", href=True)
        if "/mod/assign/view.php?id=" in a["href"]
    ]

def check_pending_submissions(url):
    """Проверяет, есть ли работы на проверке в задании."""
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    for row in soup.find_all("tr", class_="lastrow"):
        if row.find("th", class_="cell c0", string="Требуют оценки"):
            td = row.find("td", class_="cell c1 lastcol")
            if td and td.text.strip().isdigit():
                return int(td.text.strip())
    return 0

def main():
    try:
        # Получаем данные от пользователя
        username, password, course_id = get_credentials()
        login_url = "https://e.vyatsu.ru/login/index.php"
        course_url = f"https://e.vyatsu.ru/course/view.php?id={course_id}"

        # Авторизация
        print("\n🔒 Авторизация...")
        login_to_moodle(login_url, username, password)

        # Поиск заданий
        print("🔎 Поиск заданий...")
        assignments = extract_assignments(course_url)
        if not assignments:
            print("❌ Задания не найдены.")
            return

        # Проверка каждого задания
        pending_assignments = []
        for assignment in assignments:
            print(f"  • Проверка: {assignment['name']}", end="", flush=True)
            count = check_pending_submissions(assignment["url"])
            if count > 0:
                pending_assignments.append({**assignment, "count": count})
                print(f" → Найдено: {count} работ")
            else:
                print(" → Нет работ")

        # Вывод результатов
        if pending_assignments:
            print("\n📌 Задания на проверку:")
            for task in pending_assignments:
                print(f"  • {task['name']} ({task['count']} работ)")
                print(f"    → {task['url']}\n")
        else:
            print("\n✅ Все задания проверены.")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

if __name__ == "__main__":
    main()