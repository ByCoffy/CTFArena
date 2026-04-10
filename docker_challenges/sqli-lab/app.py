from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <title>CyberShop - Products</title>
    <style>
        body { background: #1a1a2e; color: #eee; font-family: monospace; padding: 20px; }
        h1 { color: #00ff88; }
        input { background: #16213e; color: #eee; border: 1px solid #0f3460; padding: 8px; margin: 5px; }
        button { background: #00ff88; color: #000; border: none; padding: 8px 16px; cursor: pointer; }
        table { border-collapse: collapse; width: 100%; margin-top: 10px; }
        th, td { border: 1px solid #333; padding: 8px; text-align: left; }
        th { background: #16213e; color: #00ff88; }
        .error { color: #ff4444; }
        .hint { color: #888; font-size: 0.9em; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>🛒 CyberShop</h1>
    <p>Search for products in our hacking store:</p>
    <form method="GET" action="/search">
        <input type="text" name="q" placeholder="Search products..." value="{{ query or '' }}">
        <button type="submit">Search</button>
    </form>
    {% if error %}
    <p class="error">Error: {{ error }}</p>
    {% endif %}
    {% if results is not none %}
    <table>
        <tr><th>ID</th><th>Name</th><th>Description</th><th>Price</th></tr>
        {% for row in results %}
        <tr><td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>${{ row[3] }}</td></tr>
        {% endfor %}
    </table>
    {% if not results %}
    <p>No products found.</p>
    {% endif %}
    {% endif %}
    <p class="hint">💡 Hint: The database might contain more tables than you think...</p>
</body>
</html>'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    try:
        conn = sqlite3.connect('/app/database.db')
        c = conn.cursor()
        # VULNERABLE: Direct string concatenation - SQL Injection!
        sql = f"SELECT * FROM products WHERE name LIKE '%{query}%'"
        c.execute(sql)
        results = c.fetchall()
        conn.close()
        return render_template_string(HTML_TEMPLATE, results=results, query=query)
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, error=str(e), query=query)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
