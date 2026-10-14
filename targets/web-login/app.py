import sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)
DB = "/tmp/app.db"


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS users")
    c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    c.execute("INSERT INTO users (username, password) VALUES ('admin', 'flagpw')")
    c.execute("INSERT INTO users (username, password) VALUES ('henry', 'password123')")
    conn.commit()
    conn.close()


PAGE = """
<!doctype html><title>Arena Login</title>
<h2>Login</h2>
<form method="post">
  <input name="username" placeholder="username">
  <input name="password" type="password" placeholder="password">
  <button>Sign in</button>
</form>
{% if msg %}<p><b>{{ msg }}</b></p>{% endif %}
"""


@app.route("/", methods=["GET", "POST"])
def login():
    msg = ""
    if request.method == "POST":
        user = request.form.get("username", "")
        pw = request.form.get("password", "")
        query = "SELECT username FROM users WHERE username = '" + user + "' AND password = '" + pw + "'"
        conn = sqlite3.connect(DB)
        try:
            row = conn.execute(query).fetchone()
        except sqlite3.Error as e:
            row, msg = None, "SQL error: " + str(e)
        conn.close()
        if row:
            msg = "Welcome, " + row[0] + "! Flag: ARENA{sqli_auth_bypass}"
        elif not msg:
            msg = "Invalid credentials."
    return render_template_string(PAGE, msg=msg)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
