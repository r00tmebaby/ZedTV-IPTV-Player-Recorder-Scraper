import json
from datetime import datetime, timezone
from typing import Optional

from config import ACCOUNTS_FILE, AccountChoice, ICON
from app import (
    _epoch_to_str,
    _normalize_base,
    _xtream_api,
    _fmt_yesno,
    _fmt_formats,
)
import PySimpleGUI as sg


def _format_account_info(info: dict) -> str:
    ui = info.get("user_info", {})
    si = info.get("server_info", {})
    allowed = ", ".join(ui.get("allowed_output_formats", [])) or "-"
    return (
        "=== USER INFO ===\n"
        f"username: {ui.get('username','')}\n"
        f"password: {ui.get('password','')}\n"
        f"auth: {ui.get('auth','')}\n"
        f"status: {ui.get('status','')}\n"
        f"is_trial: {ui.get('is_trial','')}\n"
        f"active_cons: {ui.get('active_cons','')}\n"
        f"max_connections: {ui.get('max_connections','')}\n"
        f"created_at: {ui.get('created_at','')}  ({_epoch_to_str(ui.get('created_at'))})\n"
        f"exp_date: {ui.get('exp_date','')}  ({_epoch_to_str(ui.get('exp_date'))})\n"
        f"allowed_output_formats: {allowed}\n\n"
        "=== SERVER INFO ===\n"
        f"url: {si.get('url','')}\n"
        f"server_protocol: {si.get('server_protocol','')}\n"
        f"port: {si.get('port','')}\n"
        f"https_port: {si.get('https_port','')}\n"
        f"rtmp_port: {si.get('rtmp_port','')}\n"
        f"timezone: {si.get('timezone','')}\n"
        f"time_now: {si.get('time_now','')}\n"
        f"timestamp_now: {si.get('timestamp_now','')}\n"
    )


def _accounts_load() -> dict:
    try:
        if ACCOUNTS_FILE.exists():
            return json.loads(ACCOUNTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _choose_account_window() -> Optional[AccountChoice]:
    accs = _accounts_load()

    headings = [
        "Name",
        "User",
        "Base",
        "Status",
        "Conns",
        "Expires",
        "Trial",
        "Formats",
    ]
    col_widths = [16, 14, 30, 9, 10, 20, 7, 24]

    def _rows_from_saved():
        rows = []
        for name, a in sorted(accs.items()):
            rows.append(_snapshot_to_row(name, a))
        return rows

    layout = [
        [
            sg.Table(
                values=_rows_from_saved(),
                headings=headings,
                key="_acc_table_",
                auto_size_columns=False,
                col_widths=col_widths,
                justification="l",
                expand_x=True,
                expand_y=True,
                select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                num_rows=12,
            )
        ],
        [
            sg.Button("Use"),
            sg.Button("Details"),
            sg.Button("Delete"),
            sg.Button("Refresh Snapshot"),  # <- manual re-pull if you want
            sg.Button("Close"),
        ],
    ]
    w = sg.Window(
        "Xtream Accounts",
        layout,
        modal=True,
        keep_on_top=True,
        resizable=True,
        icon=ICON,
    )

    while True:
        e, v = w.read()
        if e in (sg.WIN_CLOSED, "Close"):
            w.close()
            return None

        # selection is a list of row indexes; guard for empty
        sel_list = v.get("_acc_table_") or []
        sel = sel_list[0] if sel_list else None
        name = None
        if sel is not None:
            # get current table values and pull the first column (Name)
            table_values = w["_acc_table_"].get()
            if 0 <= sel < len(table_values):
                name = table_values[sel][0]

        if e == "Use" and name:
            w.close()
            return ("use", name, accs[name])

        if e == "Delete" and name:
            del accs[name]
            _accounts_save_all(accs)
            w["_acc_table_"].update(values=_rows_from_saved())

        if e == "Details" and name:
            a = accs[name]
            info = a.get("snapshot") or {"user_info": {}, "server_info": {}}
            sg.popup_scrolled(
                _format_account_info(info),
                title=f"Account '{name}' Details",
                keep_on_top=True,
                non_blocking=False,
            )

        if e == "Refresh Snapshot" and name:
            try:
                _refresh_snapshot_now(name, accs[name])
                accs = _accounts_load()
                w["_acc_table_"].update(values=_rows_from_saved())
                sg.popup_ok("Snapshot refreshed.", keep_on_top=True)
            except Exception as ex:
                sg.popup_error(f"Refresh failed: {ex}", keep_on_top=True)


def _snapshot_to_row(name: str, acc: dict) -> list[str]:
    """
    Build Accounts table row from saved JSON snapshot (no network).
    Columns: Name, User, Base, Status, Conns, Expires, Trial, Formats
    """
    snap = acc.get("snapshot") or {}
    ui = snap.get("user_info") or {}
    status = ui.get("status", "-")
    conns = f"{ui.get('active_cons','0')}/{ui.get('max_connections','-')}"
    exp = _epoch_to_str(ui.get("exp_date"))
    trial = _fmt_yesno(ui.get("is_trial"))
    fmts = _fmt_formats(ui)
    return [
        name,
        acc.get("username", ""),
        acc.get("base", ""),
        status,
        conns,
        exp,
        trial,
        fmts,
    ]


def _save_snapshot(name: str, acc: dict, info: dict) -> None:
    """Persist a fresh snapshot into the accounts JSON (merges into account)."""
    d = _accounts_load()
    acc = {
        **acc,
        "snapshot": {
            **(info or {}),
            "_fetched_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    d[name] = acc
    _accounts_save_all(d)


def _refresh_snapshot_now(name: str, acc: dict) -> dict:
    """Refetch from API and update saved snapshot for that account. Returns info dict."""
    info = _xtream_api(acc["base"], acc["username"], acc["password"])
    _save_snapshot(name, acc, info)
    return info


def _accounts_save_all(d: dict) -> None:
    ACCOUNTS_FILE.write_text(json.dumps(d, indent=2), encoding="utf-8")


def _accounts_save_one(name: str, acc: dict) -> None:
    d = _accounts_load()
    d[name] = acc
    _accounts_save_all(d)


def _add_account_window():
    layout = [
        [sg.Text("Name", size=(20, 1)), sg.Input(key="_name_", size=(30, 1))],
        [
            sg.Text("Host (e.g. likan.me)", size=(20, 1)),
            sg.Input(key="_host_", default_text="likan.me", size=(30, 1)),
        ],
        [
            sg.Text("Port", size=(20, 1)),
            sg.Input(key="_port_", size=(10, 1), default_text="80"),
            sg.Checkbox("Use HTTPS", key="_https_"),
        ],
        [
            sg.Text("Username", size=(20, 1)),
            sg.Input(key="_user_", default_text="36WGTJE", size=(30, 1)),
        ],
        [
            sg.Text("Password", size=(20, 1)),
            sg.Input(
                key="_pass_",
                password_char="*",
                default_text="U5LXEBV",
                size=(30, 1),
            ),
        ],
        [
            sg.Col(
                [[sg.Button("Test & Save"), sg.Button("Cancel")]],
                justification="right",
                pad=(0, 10),
            )
        ],
    ]
    w = sg.Window("Add Xtream Account", layout, modal=True, keep_on_top=True, icon=ICON)
    while True:
        e, v = w.read()
        if e in (sg.WIN_CLOSED, "Cancel"):
            w.close()
            return None
        if e == "Test & Save":
            try:
                base = _normalize_base(
                    v["_host_"],
                    int(v["_port_"]) if v["_port_"] else None,
                    v["_https_"],
                )
                info = _xtream_api(base, v["_user_"], v["_pass_"])
                if info.get("user_info", {}).get("auth") == 1:
                    name = v["_name_"] or v["_user_"]
                    acc = {
                        "base": base,
                        "username": v["_user_"],
                        "password": v["_pass_"],
                        # 🚩 Save full API reply as a snapshot for instant table rendering later
                        "snapshot": {
                            **info,
                            "_fetched_at": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                    _accounts_save_one(name, acc)

                    # Show full account details (from snapshot we just saved)
                    sg.popup_scrolled(
                        _format_account_info(info),
                        title=f"Account '{name}' Details",
                        keep_on_top=True,
                        non_blocking=False,
                    )
                    sg.popup_ok(f"Saved account '{name}'.", keep_on_top=True)
                    w.close()
                    return {"name": name, **acc}

                else:
                    sg.popup_error("Auth failed (not Active?).", keep_on_top=True)
            except Exception as ex:
                sg.popup_error(f"Error: {ex}", keep_on_top=True)
