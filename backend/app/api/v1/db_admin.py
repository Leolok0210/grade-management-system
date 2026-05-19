from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from pydantic import BaseModel
from app.database import get_db
from app.deps import require_role

router = APIRouter(prefix="/admin/db", tags=["資料庫管理"])


@router.get("/", response_class=HTMLResponse)
async def db_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>成績管理系統 - 資料庫管理</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f0f2f5; }
            .header { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { font-size: 20px; }
            .header .user { font-size: 13px; opacity: 0.9; }
            .login-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: linear-gradient(135deg, #667eea, #764ba2); display: flex; justify-content: center; align-items: center; z-index: 999; }
            .login-card { background: #fff; border-radius: 16px; padding: 40px; width: 360px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
            .login-card h2 { text-align: center; margin-bottom: 8px; font-size: 24px; }
            .login-card p { text-align: center; color: #888; margin-bottom: 24px; font-size: 14px; }
            .login-card input { width: 100%; padding: 12px 16px; border: 1px solid #ddd; border-radius: 8px; font-size: 15px; margin-bottom: 12px; outline: none; }
            .login-card button { width: 100%; padding: 12px; border: none; border-radius: 8px; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; font-size: 16px; font-weight: 600; cursor: pointer; }
            .login-card .error { color: #e74c3c; font-size: 13px; text-align: center; margin-top: 8px; }
            .container { max-width: 1200px; margin: 24px auto; padding: 0 24px; }
            .card { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
            .card h2 { font-size: 16px; margin-bottom: 12px; color: #333; }
            .stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
            .stat { background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; }
            .stat .num { font-size: 28px; font-weight: 700; color: #667eea; }
            .stat .label { font-size: 13px; color: #888; margin-top: 4px; }
            table { width: 100%; border-collapse: collapse; font-size: 14px; }
            th { background: #f5f6fa; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #eee; white-space: nowrap; }
            td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
            tr:hover td { background: #f8f9ff; }
            .tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
            .tab { padding: 8px 16px; border-radius: 20px; border: 1px solid #ddd; background: #fff; cursor: pointer; font-size: 13px; }
            .tab.active { background: #667eea; color: #fff; border-color: #667eea; }
            .sql-input { width: 100%; min-height: 80px; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-family: monospace; font-size: 14px; resize: vertical; }
            .btn { padding: 8px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }
            .btn-primary { background: #667eea; color: #fff; }
            .btn-primary:hover { background: #5a6fd6; }
            .result-area { margin-top: 12px; overflow-x: auto; }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div id="login-overlay" class="login-overlay">
            <div class="login-card">
                <h2>資料庫管理</h2>
                <p>請登入管理員帳號</p>
                <input id="username" placeholder="帳號" value="admin">
                <input id="password" type="password" placeholder="密碼" value="123456">
                <button onclick="doLogin()">登入</button>
                <div id="login-error" class="error"></div>
            </div>
        </div>
        <div id="main-app" class="hidden">
            <div class="header">
                <h1>資料庫管理</h1>
                <div class="user" id="user-info"></div>
            </div>
            <div class="container">
                <div id="stats" class="stats"></div>
                <div class="card">
                    <h2>資料表</h2>
                    <div id="tabs" class="tabs"></div>
                    <div id="table-content"></div>
                </div>
                <div class="card">
                    <h2>SQL 查詢</h2>
                    <textarea id="sql-input" class="sql-input" placeholder="SELECT * FROM users LIMIT 10;"></textarea>
                    <div style="margin-top:8px;">
                        <button class="btn btn-primary" onclick="runSQL()">執行</button>
                    </div>
                    <div id="sql-result" class="result-area"></div>
                </div>
            </div>
        </div>
        <script>
            const API = '/api/v1';
            let TOKEN = localStorage.getItem('db_admin_token') || '';
            let currentTable = '';

            async function doLogin() {
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                try {
                    const resp = await fetch(API + '/auth/login', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({username, password})
                    });
                    const data = await resp.json();
                    if (!resp.ok) {
                        document.getElementById('login-error').textContent = data.detail || '登入失敗';
                        return;
                    }
                    if (data.user.role !== 'admin') {
                        document.getElementById('login-error').textContent = '需要管理員權限';
                        return;
                    }
                    TOKEN = data.access_token;
                    localStorage.setItem('db_admin_token', TOKEN);
                    document.getElementById('login-overlay').classList.add('hidden');
                    document.getElementById('main-app').classList.remove('hidden');
                    document.getElementById('user-info').textContent = data.user.name + ' (' + data.user.role + ')';
                    loadStats();
                    loadTables();
                } catch(e) {
                    document.getElementById('login-error').textContent = '連線錯誤';
                }
            }

            async function apiFetch(url, options = {}) {
                options.headers = options.headers || {};
                options.headers['Authorization'] = 'Bearer ' + TOKEN;
                const resp = await fetch(url, options);
                if (resp.status === 401) {
                    localStorage.removeItem('db_admin_token');
                    location.reload();
                }
                return resp;
            }

            async function loadStats() {
                const resp = await apiFetch(API + '/admin/db/stats');
                const data = await resp.json();
                document.getElementById('stats').innerHTML = data.map(s =>
                    `<div class="stat"><div class="num">${s.count}</div><div class="label">${s.table}</div></div>`
                ).join('');
            }

            async function loadTables() {
                const resp = await apiFetch(API + '/admin/db/tables');
                const tables = await resp.json();
                document.getElementById('tabs').innerHTML = tables.map(t =>
                    `<div class="tab ${t === currentTable ? 'active' : ''}" onclick="loadTable('${t}')">${t}</div>`
                ).join('');
                if (!currentTable && tables.length > 0) loadTable(tables[0]);
            }

            async function loadTable(name) {
                currentTable = name;
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                event.target.classList.add('active');
                const resp = await apiFetch(API + '/admin/db/table/' + name + '?limit=50');
                const data = await resp.json();
                const el = document.getElementById('table-content');
                if (!data.columns || !data.rows) { el.innerHTML = '<p>無資料</p>'; return; }
                let html = '<table><thead><tr>';
                data.columns.forEach(c => html += `<th>${c}</th>`);
                html += '</tr></thead><tbody>';
                data.rows.forEach(row => {
                    html += '<tr>';
                    row.forEach(cell => {
                        let val = cell === null ? '<span style="color:#ccc">NULL</span>' : String(cell);
                        html += `<td title="${val}">${val}</td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
                html += `<p style="margin-top:8px;color:#888;font-size:13px;">共 ${data.rows.length} 筆（最多顯示50筆）</p>`;
                el.innerHTML = html;
            }

            async function runSQL() {
                const sql = document.getElementById('sql-input').value.trim();
                if (!sql) return;
                const resp = await apiFetch(API + '/admin/db/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({sql})
                });
                const data = await resp.json();
                const el = document.getElementById('sql-result');
                if (data.error) { el.innerHTML = `<p style="color:red">${data.error}</p>`; return; }
                if (!data.columns) { el.innerHTML = `<p>執行成功，影響 ${data.rowcount || 0} 行</p>`; return; }
                let html = '<table><thead><tr>';
                data.columns.forEach(c => html += `<th>${c}</th>`);
                html += '</tr></thead><tbody>';
                data.rows.forEach(row => {
                    html += '<tr>';
                    row.forEach(cell => {
                        let val = cell === null ? '<span style="color:#ccc">NULL</span>' : String(cell);
                        html += `<td title="${val}">${val}</td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
                el.innerHTML = html;
            }

            // Auto-login if token exists
            if (TOKEN) {
                apiFetch(API + '/admin/db/tables').then(resp => {
                    if (resp.ok) {
                        document.getElementById('login-overlay').classList.add('hidden');
                        document.getElementById('main-app').classList.remove('hidden');
                        loadStats();
                        loadTables();
                    } else {
                        localStorage.removeItem('db_admin_token');
                    }
                });
            }
        </script>
    </body>
    </html>
    """


def _get_tables_and_views(db):
    """取得所有資料表和視圖（排除已被視圖取代的原表）"""
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    # PostgreSQL: 查詢視圖
    try:
        views_result = db.execute(text(
            "SELECT viewname FROM pg_views WHERE schemaname = 'public'"
        )).fetchall()
        views = [r[0] for r in views_result]
    except Exception:
        views = []
    all_items = sorted(tables + views)
    # 被視圖取代的原表不顯示
    hidden = {"daily_grades"}
    return [t for t in all_items if t not in hidden]


@router.get("/stats")
async def db_stats(db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    tables = _get_tables_and_views(db)
    result = []
    for t in sorted(tables):
        count = db.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
        result.append({"table": t, "count": count})
    return result


@router.get("/tables")
async def list_tables(db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    return _get_tables_and_views(db)


@router.get("/table/{table_name}")
async def get_table_data(
    table_name: str,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    all_names = _get_tables_and_views(db)
    if table_name not in all_names:
        return {"error": "資料表不存在"}

    # 嘗試取得欄位（table 和 view 都適用）
    try:
        inspector = inspect(db.bind)
        columns = [c["name"] for c in inspector.get_columns(table_name)]
    except Exception:
        result = db.execute(text(f'SELECT * FROM "{table_name}" LIMIT 0'))
        columns = list(result.keys())
    rows = db.execute(text(f'SELECT * FROM "{table_name}" LIMIT :lim'), {"lim": limit}).fetchall()

    return {
        "columns": columns,
        "rows": [list(r) for r in rows],
    }


class SQLQuery(BaseModel):
    sql: str


@router.post("/query")
async def run_query(req: SQLQuery, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    sql = req.sql.strip()
    if not sql.upper().startswith("SELECT"):
        return {"error": "只允許 SELECT 查詢"}

    try:
        result = db.execute(text(sql))
        columns = list(result.keys())
        rows = [list(r) for r in result.fetchall()]
        return {"columns": columns, "rows": rows}
    except Exception as e:
        return {"error": str(e)}