import sqlite3

def setup():
    conn = sqlite3.connect('/app/database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        price REAL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS secret_flags (
        id INTEGER PRIMARY KEY,
        flag TEXT NOT NULL
    )''')

    # Insert sample data
    c.execute("INSERT INTO users VALUES (1, 'admin', 'sup3rs3cur3p4ss', 'admin')")
    c.execute("INSERT INTO users VALUES (2, 'guest', 'guest123', 'user')")
    c.execute("INSERT INTO users VALUES (3, 'john', 'password123', 'user')")

    c.execute("INSERT INTO products VALUES (1, 'Hacking Book', 'Learn ethical hacking', 29.99)")
    c.execute("INSERT INTO products VALUES (2, 'USB Rubber Ducky', 'Keystroke injection tool', 49.99)")
    c.execute("INSERT INTO products VALUES (3, 'WiFi Pineapple', 'Network auditing tool', 99.99)")

    # The flag!
    c.execute("INSERT INTO secret_flags VALUES (1, 'FLAG{sql_1nj3ct10n_m4st3r_2025}')")

    conn.commit()
    conn.close()
    print("[+] Database setup complete")

if __name__ == '__main__':
    setup()
