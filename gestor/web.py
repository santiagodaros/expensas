"""
Gestor de Consorcios - Web Report Generation
Generates HTML index and per-period reports, and pushes to GitHub/Vercel.
"""
import os
import subprocess
from datetime import datetime

from gestor.helpers import WEB_DIR, _MESES, _tf, _fmt, _pl_of
from gestor.db import get_cfg


def generar_html_index():
    """Genera web_reportes/index.html con links a todos los reportes disponibles."""
    reportes = []
    for cons_dir in sorted(os.listdir(WEB_DIR)):
        cons_path = os.path.join(WEB_DIR, cons_dir)
        if not os.path.isdir(cons_path) or cons_dir.startswith("."): continue
        for per_dir in sorted(os.listdir(cons_path), reverse=True):
            per_path = os.path.join(cons_path, per_dir)
            idx = os.path.join(per_path, "index.html")
            if os.path.isfile(idx):
                cons_label = cons_dir.replace("_", " ")
                try:
                    y, m = per_dir.split("-")
                    per_label = f"{_MESES[int(m)]} {y}"
                except Exception:
                    per_label = per_dir
                reportes.append((cons_label, per_label, f"{cons_dir}/{per_dir}/index.html"))

    rows = ""; cons_actual = None
    for cons_label, per_label, href in reportes:
        if cons_label != cons_actual:
            if cons_actual is not None:
                rows += "</tbody></table></div>"
            rows += (
                '<div class="cons-block"><h2>' + cons_label +
                '</h2><table><thead><tr><th>Periodo</th><th>Reporte</th></tr></thead><tbody>'
            )
            cons_actual = cons_label
        rows += f'<tr><td>{per_label}</td><td><a href="{href}">Ver reporte</a></td></tr>'
    if cons_actual:
        rows += "</tbody></table></div>"
    if not rows:
        rows = '<p class="empty">Todavia no hay reportes generados.</p>'

    html = (
        '<!DOCTYPE html>\n<html lang="es">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>Reportes de Expensas</title>\n'
        '<style>\n'
        '  *{box-sizing:border-box;margin:0;padding:0}\n'
        '  body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}\n'
        '  header{background:#1e293b;padding:28px 40px;border-bottom:2px solid #334155}\n'
        '  header h1{font-size:1.6rem;color:#60a5fa;font-weight:700}\n'
        '  header p{color:#94a3b8;margin-top:4px;font-size:.9rem}\n'
        '  main{max-width:860px;margin:40px auto;padding:0 24px}\n'
        '  .cons-block{background:#1e293b;border-radius:12px;padding:24px;margin-bottom:24px;border:1px solid #334155}\n'
        '  .cons-block h2{color:#93c5fd;font-size:1.1rem;margin-bottom:16px;padding-bottom:10px;border-bottom:1px solid #334155}\n'
        '  table{width:100%;border-collapse:collapse}\n'
        '  th{text-align:left;padding:8px 12px;font-size:.8rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em}\n'
        '  td{padding:10px 12px;border-top:1px solid #1e3a5f}\n'
        '  tr:hover td{background:#172554}\n'
        '  a{color:#60a5fa;text-decoration:none;font-weight:500}\n'
        '  a:hover{color:#93c5fd;text-decoration:underline}\n'
        '  .empty{color:#64748b;text-align:center;padding:40px}\n'
        '  footer{text-align:center;color:#475569;font-size:.8rem;padding:32px}\n'
        '</style>\n</head>\n<body>\n'
        '<header><h1>Reportes de Expensas</h1><p>Todos los periodos disponibles</p></header>\n'
        '<main>' + rows + '</main>\n'
        '<footer>Generado automaticamente por Gestor de Consorcios</footer>\n'
        '</body>\n</html>'
    )
    idx_path = os.path.join(WEB_DIR, "index.html")
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(html)
    return idx_path


def _git_push_web(log_cb=None):
    """
    Hace git add/commit/push del directorio WEB_DIR al repositorio
    configurado. Requiere que 'git' este instalado y que el usuario
    haya configurado git_repo_url y git_token en Configuracion.
    Retorna (ok: bool, msg: str).
    """
    repo_url = get_cfg("git_repo_url", "").strip()
    token    = get_cfg("git_token",    "").strip()
    if not repo_url:
        return False, "No hay URL de repositorio configurada (Configuracion - GitHub/Vercel)."

    if token and "https://" in repo_url and "@" not in repo_url:
        repo_url_auth = repo_url.replace("https://", f"https://{token}@")
    else:
        repo_url_auth = repo_url

    def run(cmd, cwd=WEB_DIR):
        if log_cb: log_cb(f"$ {' '.join(cmd)}")
        _flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60, creationflags=_flags)
        if log_cb and r.stdout.strip(): log_cb(r.stdout.strip())
        if log_cb and r.stderr.strip(): log_cb(r.stderr.strip())
        return r

    try:
        if not os.path.isdir(os.path.join(WEB_DIR, ".git")):
            run(["git", "init"])
            run(["git", "branch", "-M", "main"])

        remote_check = run(["git", "remote"])
        if "origin" in remote_check.stdout:
            run(["git", "remote", "set-url", "origin", repo_url_auth])
        else:
            run(["git", "remote", "add", "origin", repo_url_auth])

        run(["git", "config", "user.email", "app@consorcios.local"])
        run(["git", "config", "user.name",  "Gestor Consorcios"])
        run(["git", "add", "-A"])

        status = run(["git", "status", "--porcelain"])
        if not status.stdout.strip():
            return True, "Sin cambios nuevos para publicar."

        from datetime import datetime as _dt
        msg = f"Actualizar reportes {_dt.now().strftime('%Y-%m-%d %H:%M')}"
        commit_r = run(["git", "commit", "-m", msg])
        if commit_r.returncode != 0:
            return False, f"Error en commit: {commit_r.stderr}"

        push_r = run(["git", "push", "-u", "origin", "main"])
        if push_r.returncode != 0:
            if "rejected" in push_r.stderr or "failed to push" in push_r.stderr:
                # Intentar rebase antes de rendirse (nunca force-push)
                rebase_r = run(["git", "pull", "--rebase", "origin", "main"])
                if rebase_r.returncode == 0:
                    push_r = run(["git", "push", "-u", "origin", "main"])
            if push_r.returncode != 0:
                return False, f"Error en push: {push_r.stderr[:200]}"

        return True, "Publicado en GitHub/Vercel correctamente."
    except FileNotFoundError:
        return False, "Git no encontrado. Instala Git desde https://git-scm.com y reinicia la app."
    except subprocess.TimeoutExpired:
        return False, "Timeout al hacer push. Verifica tu conexion a internet."
    except Exception as e:
        return False, str(e)


def generar_html_reporte(cons, gs_list, per, folder):
    cn = {
        "A": get_cfg("nombre_cat_a", "Gastos Comunes"),
        "B": get_cfg("nombre_cat_b", "Fuerza Motriz"),
        "C": get_cfg("nombre_cat_c", "Locales"),
    }
    rows_html = ""; total_general = 0.0
    for cat in ["A", "B", "C"]:
        cat_gs = [g for g in gs_list if g.get("categoria") == cat]
        if not cat_gs: continue
        sub = 0.0
        for g in cat_gs:
            m = _tf(g.get("monto", 0)); sub += m
            comp = g.get("comprobante_path") or ""
            doc = ""
            if comp and os.path.isfile(comp):
                rel = "comprobantes/" + os.path.basename(comp)
                doc = f'<a href="{rel}" target="_blank" class="doc-link" title="Ver comprobante">&#128196;</a>'
            rows_html += (
                f'<tr><td class="cat">{cat}</td>'
                f'<td class="desc">{g.get("descripcion","")}</td>'
                f'<td class="monto">${_fmt(m) if m else "0,00"}</td>'
                f'<td class="doc">{doc}</td></tr>\n'
            )
        total_general += sub
        rows_html += (
            f'<tr class="subtotal"><td colspan="2">Subtotal {cat} &mdash; {cn[cat]}</td>'
            f'<td class="monto">${_fmt(sub) if sub else "0,00"}</td><td></td></tr>\n'
        )
    tot_str = _fmt(total_general) if total_general else "0,00"
    pl = _pl_of(per)
    ts = datetime.now().strftime('%d/%m/%Y %H:%M')
    html = (
        '<!DOCTYPE html>\n<html lang="es">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>Expensas {cons["nombre"]} &mdash; {pl}</title>\n'
        '<style>\n'
        '  *{box-sizing:border-box;margin:0;padding:0}\n'
        '  body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}\n'
        '  header{background:#1e293b;padding:28px 40px;border-bottom:2px solid #334155}\n'
        '  header h1{font-size:1.5rem;color:#60a5fa;font-weight:700}\n'
        '  header p{color:#94a3b8;margin-top:6px;font-size:.92rem}\n'
        '  header p strong{color:#e2e8f0}\n'
        '  .back{display:inline-block;margin:20px 40px 0;color:#60a5fa;font-size:.85rem;text-decoration:none}\n'
        '  .back:hover{color:#93c5fd}\n'
        '  main{max-width:980px;margin:24px auto;padding:0 24px}\n'
        '  .card{background:#1e293b;border-radius:12px;border:1px solid #334155;padding:28px 32px}\n'
        '  h2{font-size:.85rem;color:#94a3b8;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #334155;text-transform:uppercase;letter-spacing:.06em}\n'
        '  table{width:100%;border-collapse:collapse;font-size:.92rem}\n'
        '  th{background:#1e3a5f;color:#93c5fd;padding:10px 14px;text-align:left;font-weight:600;font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}\n'
        '  th.monto,td.monto{text-align:right;white-space:nowrap}\n'
        '  th.doc,td.doc{text-align:center;width:52px}\n'
        '  th.cat,td.cat{width:52px;text-align:center;font-weight:700;color:#60a5fa}\n'
        '  td{padding:10px 14px;border-bottom:1px solid #1e3a5f;color:#e2e8f0}\n'
        '  tbody tr:hover td{background:#172554}\n'
        '  tr.subtotal td{background:#172554;font-weight:600;color:#93c5fd;border-top:1px solid #2d4a7a;border-bottom:1px solid #2d4a7a}\n'
        '  tr.total-row td{background:#854d0e;color:#fef08a;font-weight:700;font-size:1.02rem;border-top:2px solid #a16207}\n'
        '  .doc-link{font-size:1.1rem;text-decoration:none;opacity:.75}\n'
        '  .doc-link:hover{opacity:1}\n'
        '  footer{text-align:center;color:#475569;font-size:.8rem;padding:28px}\n'
        '</style>\n</head>\n<body>\n'
        f'<header>\n  <h1>{cons["nombre"]}</h1>\n'
        f'  <p>Liquidaci&oacute;n de Gastos &nbsp;|&nbsp; Periodo: <strong>{pl}</strong></p>\n</header>\n'
        '<a class="back" href="../../index.html">&larr; Volver al inicio</a>\n'
        '<main>\n<div class="card">\n'
        '  <h2>Detalle de Gastos por Categor&iacute;a</h2>\n'
        '  <table>\n    <thead><tr>\n'
        '      <th class="cat">Cat.</th>\n'
        '      <th>Descripci&oacute;n del Gasto</th>\n'
        '      <th class="monto">Importe $</th>\n'
        '      <th class="doc">Doc</th>\n'
        '    </tr></thead>\n'
        f'    <tbody>{rows_html}</tbody>\n'
        '    <tfoot>\n      <tr class="total-row">\n'
        '        <td colspan="2"><strong>TOTAL GENERAL DE GASTOS</strong></td>\n'
        f'        <td class="monto"><strong>${tot_str}</strong></td>\n'
        '        <td></td>\n      </tr>\n    </tfoot>\n  </table>\n</div>\n</main>\n'
        f'<footer>Generado por Gestor de Consorcios &nbsp;|&nbsp; {ts}</footer>\n'
        '</body>\n</html>'
    )
    fpath = os.path.join(folder, "index.html")
    with open(fpath, "w", encoding="utf-8") as fh:
        fh.write(html)
    return fpath
