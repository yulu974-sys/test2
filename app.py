import json
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"


def init_json_file(file_path: str) -> None:
    """
    初始化 JSON 檔案。
    若檔案不存在或格式錯誤，建立預設的 users.json。
    """
    default_data = {
        "users": [
            {
                "username": "admin",
                "email": "admin@example.com",
                "password": "admin123",
                "phone": "0912345678",
                "birthdate": "1990-01-01"
            }
        ]
    }

    path = Path(file_path)

    if not path.exists():
        with open(path, "w", encoding="utf-8") as file:
            json.dump(default_data, file, ensure_ascii=False, indent=2)
        return

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict) or "users" not in data:
            raise json.JSONDecodeError("Invalid JSON structure", "", 0)

    except json.JSONDecodeError:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(default_data, file, ensure_ascii=False, indent=2)


def read_users(file_path: str) -> dict:
    """
    讀取 users.json 並回傳 dict。
    若檔案不存在或 JSON 格式錯誤，回傳空 users 結構。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {"users": []}
    except json.JSONDecodeError:
        return {"users": []}


def save_users(file_path: str, data: dict) -> bool:
    """
    將使用者資料寫入 JSON 檔案。
    成功回傳 True，失敗回傳 False。
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return True
    except FileNotFoundError:
        return False


def validate_register(form_data: dict, users: list) -> dict:
    """
    驗證註冊表單資料。
    成功回傳 {"success": True, "data": {...}}
    失敗回傳 {"success": False, "error": "錯誤訊息"}
    """
    username = form_data.get("username", "").strip()
    email = form_data.get("email", "").strip()
    password = form_data.get("password", "").strip()
    phone = form_data.get("phone", "").strip()
    birthdate = form_data.get("birthdate", "").strip()

    if not username:
        return {"success": False, "error": "帳號不可為空白。"}
    if not email:
        return {"success": False, "error": "Email 不可為空白。"}
    if not password:
        return {"success": False, "error": "密碼不可為空白。"}
    if not birthdate:
        return {"success": False, "error": "出生日期不可為空白。"}

    if "@" not in email or "." not in email:
        return {"success": False, "error": "Email 格式不正確。"}

    if not 6 <= len(password) <= 16:
        return {"success": False, "error": "密碼長度需介於 6 到 16 字元。"}

    if phone:
        if not phone.isdigit() or len(phone) != 10 or not phone.startswith("09"):
            return {"success": False, "error": "電話格式錯誤，需為 09 開頭的 10 碼數字。"}

    for user in users:
        if user.get("username") == username:
            return {"success": False, "error": "帳號已存在，請使用其他帳號。"}
        if user.get("email") == email:
            return {"success": False, "error": "Email 已被註冊，請使用其他 Email。"}

    user_data = {
        "username": username,
        "email": email,
        "password": password,
        "phone": phone,
        "birthdate": birthdate
    }

    return {"success": True, "data": user_data}


def verify_login(email: str, password: str, users: list) -> dict:
    """
    驗證登入資料。
    成功回傳 {"success": True, "data": user}
    失敗回傳 {"success": False, "error": "錯誤訊息"}
    """
    email = email.strip()
    password = password.strip()

    if not email or not password:
        return {"success": False, "error": "Email 與密碼皆不可為空白。"}

    for user in users:
        if user.get("email") == email and user.get("password") == password:
            return {"success": True, "data": user}

    return {"success": False, "error": "Email 或密碼錯誤。"}


@app.template_filter("mask_phone")
def mask_phone(phone: str) -> str:
    """
    遮罩電話號碼，中間四碼以 * 取代。
    例如：0912345678 -> 0912****78
    """
    if not phone:
        return "未提供"
    if len(phone) == 10 and phone.isdigit():
        return f"{phone[:4]}****{phone[-2:]}"
    return phone


@app.template_filter("format_tw_date")
def format_tw_date(date_str: str) -> str:
    """
    將西元日期轉為民國日期格式。
    例如：1990-01-01 -> 民國79年01月01日
    """
    if not date_str:
        return "未提供"

    parts = date_str.split("-")
    if len(parts) != 3:
        return date_str

    year, month, day = parts
    if not year.isdigit():
        return date_str

    tw_year = int(year) - 1911
    return f"民國{tw_year}年{month}月{day}日"


# 模組層級初始化，符合題目要求
init_json_file(str(USERS_FILE))


@app.route("/")
def index():
    """首頁。"""
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register_route():
    """註冊頁面與註冊處理。"""
    if request.method == "GET":
        return render_template("register.html")

    data = read_users(str(USERS_FILE))
    users = data.get("users", [])

    form_data = {
        "username": request.form.get("username", "").strip(),
        "email": request.form.get("email", "").strip(),
        "password": request.form.get("password", "").strip(),
        "phone": request.form.get("phone", "").strip(),
        "birthdate": request.form.get("birthdate", "").strip()
    }

    result = validate_register(form_data, users)

    if not result["success"]:
        return redirect(url_for("error_route", message=result["error"]))

    users.append(result["data"])
    data["users"] = users

    if save_users(str(USERS_FILE), data):
        return redirect(url_for("login_route"))

    return redirect(url_for("error_route", message="資料儲存失敗。"))


@app.route("/login", methods=["GET", "POST"])
def login_route():
    """登入頁面與登入處理。"""
    if request.method == "GET":
        return render_template("login.html")

    data = read_users(str(USERS_FILE))
    users = data.get("users", [])

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    result = verify_login(email, password, users)

    if result["success"]:
        username = result["data"]["username"]
        return redirect(url_for("welcome_route", username=username))

    return redirect(url_for("error_route", message=result["error"]))


@app.route("/welcome/<username>")
def welcome_route(username):
    """歡迎頁，依 username 顯示會員資料。"""
    data = read_users(str(USERS_FILE))
    users = data.get("users", [])

    target_user = None
    for user in users:
        if user.get("username") == username:
            target_user = user
            break

    if target_user is None:
        return redirect(url_for("error_route", message="查無此會員資料。"))

    return render_template("welcome.html", user=target_user)


@app.route("/users")
def users_list_route():
    """會員清單頁。"""
    data = read_users(str(USERS_FILE))
    users = data.get("users", [])
    return render_template("users.html", users=users)


@app.route("/error")
def error_route():
    """統一錯誤頁。"""
    message = request.args.get("message", "發生未知錯誤。")
    return render_template("error.html", message=message)


if __name__ == "__main__":
    app.run(debug=True)
