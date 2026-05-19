from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from app.database import get_db
from app.deps import require_role

router = APIRouter(prefix="/admin/db", tags=["資料庫管理"])


@router.get("/", response_class=HTMLResponse)
async def db_dashboard(current_user=Depends(require_role("admin"))):
    return """
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <title>成績管理系統 - 資料庫管理</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f0f2f5; }
            .header { background: linear-gradient(135deg, #667eea, #764ba2); color: #fff; padding: 16px 24px; }
            .header h1 { font-size: 20px; }
            .container { max-width: 1200px; margin: 24px auto; padding: 0 24px; }
            .card { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
            .card h2 { font-size: 16px; margin-bottom: 12px; color: #333; }
            .stats { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; margin-bottom: 20px; }
            .stat { background: #f8f9fa; border-radius: 8px; padding: 16px; text-align: center; }
            .stat .num { font-size: 28px; font-weight: 700; color: #667eea; }
            .stat .label { font-size: 13px; color: #888; margin-top: 4px; }
            table { width: 100%; border-collapse: collapse; font-size: 14px; }
            th { background: #f5f6fa; padding: 10px 12px; text-align: left; font-weight: 600; border-bottom: 2px solid #eee; }
            td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; }
            tr:hover td { background: #f8f9ff; }
            .tabs { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
            .tab { padding: 8px 16px; border-radius: 20px; border: 1px solid #ddd; background: #fff; cursor: pointer; font-size: 13px; }
            .tab.active { background: #667eea; color: #fff; border-color: #667eea; }
            .sql-input { width: 100%; min-height: 80px; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-family: monospace; font-size: 14px; resize: vertical; }
            .btn { padding: 8px 20px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; }
            .btn-primary { background: #667eea; color: #fff; }
            .btn-primary:hover { background: #5a6fd6; }
            .result-area { margin-top: 12px; overflow-x: auto; }
            .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 12px; }
            .badge-green { background: #e8f5e9; color: #2e7d32; }
            .badge-red { background: #ffebee; color: #c62828; }
            .badge-blue { background: #e3f2fd; color: #1565c0; }
        </style>
    </head>
    <body>
        <div class="header"><h1>資料庫管理</h1></div>
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
        <script>
            const API = '/api/v1/admin/db';
            let currentTable = '';

            async function loadStats() {
                const resp = await fetch(API + '/stats');
                const data = await resp.json();
                const el = document.getElementById('stats');
                el.innerHTML = data.map(s =>
                    `<div class="stat"><div class="num">${s.count}</div><div class="label">${s.table}</div></div>`
                ).join('');
            }

            async function loadTables() {
                const resp = await fetch(API + '/tables');
                const tables = await resp.json();
                const tabs = document.getElementById('tabs');
                tabs.innerHTML = tables.map(t =>
                    `<div class="tab ${t === currentTable ? 'active' : ''}" onclick="loadTable('${t}')">${t}</div>`
                ).join('');
                if (!currentTable && tables.length > 0) {
                    loadTable(tables[0]);
                }
            }

            async function loadTable(name) {
                currentTable = name;
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                event.target.classList.add('active');
                const resp = await fetch(API + '/table/' + name + '?limit=50');
                const data = await resp.json();
                const el = document.getElementById('table-content');
                if (!data.columns || !data.rows) { el.innerHTML = '<p>無資料</p>'; return; }
                let html = '<table><thead><tr>';
                data.columns.forEach(c => html += `<th>${c}</th>`);
                html += '</tr></thead><tbody>';
                data.rows.forEach(row => {
                    html += '<tr>';
                    row.forEach(cell => {
                        let val = cell === null ? '<span style="color:#ccc">NULL</span>' : cell;
                        html += `<td>${val}</td>`;
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
                const resp = await fetch(API + '/query', {
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
                        let val = cell === null ? '<span style="color:#ccc">NULL</span>' : cell;
                        html += `<td>${val}</td>`;
                    });
                    html += '</tr>';
                });
                html += '</tbody></table>';
                el.innerHTML = html;
            }

            loadStats();
            loadTables();
        </script>
    </body>
    </html>
    """


@router.get("/stats")
async def db_stats(db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    result = []
    for t in sorted(tables):
        count = db.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
        result.append({"table": t, "count": count})
    return result


@router.get("/tables")
async def list_tables(db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    inspector = inspect(db.bind)
    return sorted(inspector.get_table_names())


@router.get("/table/{table_name}")
async def get_table_data(
    table_name: str,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    inspector = inspect(db.bind)
    if table_name not in inspector.get_table_names():
        return {"error": "資料表不存在"}

    columns = [c["name"] for c in inspector.get_columns(table_name)]
    rows = db.execute(text(f'SELECT * FROM "{table_name}" LIMIT :lim'), {"lim": limit}).fetchall()

    return {
        "columns": columns,
        "rows": [list(r) for r in rows],
    }


class SQLQuery(BaseModel):
    sql: str


from pydantic import BaseModel


@router.post("/query")
async def run_query(req: SQLQuery, db: Session = Depends(get_db), current_user=Depends(require_role("admin"))):
    sql = req.sql.strip()
    # Only allow SELECT
    if not sql.upper().startswith("SELECT"):
        return {"error": "只允許 SELECT 查詢"}

    try:
        result = db.execute(text(sql))
        columns = list(result.keys())
        rows = [list(r) for r in result.fetchall()]
        return {"columns": columns, "rows": rows}
    except Exception as e:
        return {"error": str(e)}