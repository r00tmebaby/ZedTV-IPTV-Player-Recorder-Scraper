import asyncio
import ctypes
import os.path
import re
from pathlib import Path
from sys import platform as platform
import requests

from account import _add_account_window, _choose_account_window
from config import ICON
from layout import sg, layout
import player
from models import Data, IpModel, IPTVFileType
from settings import (
    _remember_last_m3u,
    _remember_last_account,
    _auto_restore_last,
    _load_xtream_into_app,
)
from app import (
    get_categories,
    _rows,
    generate_list,
    get_selected,
    _launch_vlc_external,
    _build_record_sout,
)

user32 = ctypes.windll.user32


async def main():
    sg.theme("DarkTeal6")
    sg.set_options(element_padding=(0, 0))
    Data.categories = get_categories()

    async def play(media_play_link: str, full_screen: bool = False) -> None:

        if Player.players is not None:
            Player.players.stop()

        Player.players.set_media(media_play_link)

        Player.players.set_xwindow(0)
        Player.players.set_hwnd(0)

        if not full_screen:
            if platform.startswith("linux"):
                Player.players.set_xwindow(
                    window["_canvas_video_"].Widget.winfo_id()
                )
            else:
                Player.players.set_hwnd(
                    window["_canvas_video_"].Widget.winfo_id()
                )

        Player.players.play()

    window = sg.Window(
        "ZED-TV IPTV Scraper @r00tme v1.4",
        layout,
        icon=ICON,
        resizable=True,
        return_keyboard_events=True,
        use_default_focus=True,
        size=(1000, 800),
        location=(user32.GetSystemMetrics(0) / 3.3, 20),
    ).finalize()
    try:
        _auto_restore_last(window)
    except Exception:
        pass

    class Player:
        vlc_instance = player.Instance(
            "streamlink --width=200 --aout=directsound"
        )
        players = vlc_instance.media_player_new()

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "Exit"):
            break
        if event == "About":
            sg.popup(
                "IPTV Player-Scraper & r00tme",
                "1.4 Released on 22.09.2025",
                no_titlebar=True,
                grab_anywhere=True,
                keep_on_top=True,
            )
        elif event == "Open":
            Data.filename = sg.popup_get_file(
                message="file to open",
                file_types=IPTVFileType.all_types(),
                default_path=os.getcwd(),
                no_window=True,
            )
            Data.categories = get_categories()
            window["_table_countries_"].update(_rows(Data.categories))
        elif event == "Open":
            Data.filename = sg.popup_get_file(
                message="file to open",
                default_path=os.getcwd(),
                file_types=IPTVFileType.all_types(),
                no_window=True,
            )
            if Data.filename:
                Data.categories = get_categories()
                window["_table_countries_"].update(_rows(Data.categories))
                _remember_last_m3u(Data.filename)
        elif (
            event == "Custom List"
            and Data.filename
            and values["_table_countries_"]
        ):
            generate_window = sg.Window(
                "IP Address Info",
                layout=[
                    [
                        sg.SaveAs(
                            "Save as",
                            target="_file_",
                            key="_file_to_be_generated_",
                        ),
                        sg.I(key="_file_", disabled=True),
                        sg.B("Create", key="_create_list_"),
                    ]
                ],
                icon=ICON,
            ).finalize()
            while True:
                generate_event, generate_values = generate_window.read()
                if generate_event in (sg.WIN_CLOSED, "Exit"):
                    break
                if (
                    Path(generate_values["_file_to_be_generated_"])
                    and generate_event == "_create_list_"
                ):
                    asyncio.ensure_future(
                        generate_list(
                            values=values,
                            categories=Data.categories,
                            new_file=generate_values["_file_to_be_generated_"],
                            do_file=True,
                        ),
                        loop=asyncio.get_event_loop(),
                    )
                    sg.popup_ok(
                        f'Custom list {generate_values["_file_to_be_generated_"]} has been created',
                        no_titlebar=True,
                    )
        # --- Xtream menu ---
        elif event == "Add Account":
            acc = _add_account_window()
            if acc:
                Data.xtream_account = acc
                _remember_last_account(acc.get("name") or acc["username"])
                _load_xtream_into_app(
                    window, acc["base"], acc["username"], acc["password"]
                )
                sg.popup("Xtream list loaded.", keep_on_top=True)

        elif event == "Accounts...":
            choice = _choose_account_window()
            if choice and choice[0] == "use":
                _, name, acc = choice
                Data.xtream_account = {"name": name, **acc}
                _remember_last_account(name)
                _load_xtream_into_app(
                    window, acc["base"], acc["username"], acc["password"]
                )
                sg.popup(f"Using account: {name}", keep_on_top=True)

        elif (
            event == "Reload from Current" and Data.xtream_account is not None
        ):
            acc = Data.xtream_account
            if acc:
                _load_xtream_into_app(
                    window, acc["base"], acc["username"], acc["password"]
                )
            else:
                sg.popup_error(
                    "No current Xtream account. Use Xtream → Add Account first.",
                    keep_on_top=True,
                )

        elif event == "IP Info":
            ipinfo_layout = [
                [
                    sg.Col(
                        [
                            [
                                sg.T(
                                    key="_ip_address_info_",
                                    text=IpModel(**Data.ip_info).get_results,
                                )
                            ],
                        ],
                        expand_y=True,
                        expand_x=True,
                    ),
                ]
            ]
            ipinfo_window = sg.Window(
                "IP Address Info",
                ipinfo_layout,
                icon="media/ico.ico",
                size=(300, 150),
            )

            while True:
                ipinfo_event, ipinfo_values = ipinfo_window.read()
                if ipinfo_event in (sg.WIN_CLOSED, "Exit"):
                    break
                try:
                    Data.ip_info = requests.get("http://ipinfo.io/json").json()
                except ConnectionError:
                    continue
                ipinfo_window["_ip_address_info_"].Update(
                    IpModel(**Data.ip_info).get_results
                )

        elif event == "_table_countries_" and Data.categories:
            Data.selected_list = await generate_list(values, Data.categories)
            window["_iptv_content_"].update(await get_selected())
        elif event == "Stop":
            Player.players.stop()
        elif (
            event in ["_iptv_content_", "Record", "Full Screen", "Play in VLC"]
            and len(values["_iptv_content_"]) == 1
        ):
            media_link = [i.split("\n")[1] for i in Data.selected_list][
                values["_iptv_content_"][0]
            ]
            # Extract channel/movie title from EXTINF
            title = re.findall(
                r'tvg-name="(.*?)"',
                [i.split("\n")[0] for i in Data.selected_list][
                    values["_iptv_content_"][0]
                ],
            )[0].replace("|", "")

            if event == "Play in VLC":
                _launch_vlc_external(media_link)
                Player.players.stop()
                continue

            if event == "Record":
                sout = _build_record_sout(title)
                Data.media_instance = Player.vlc_instance.media_new(
                    media_link, sout
                )
            else:
                # just play (normal or full screen)
                Data.media_instance = Player.vlc_instance.media_new(media_link)
            if event == "Full Screen":
                await asyncio.ensure_future(play(Data.media_instance, True))
            else:
                await asyncio.ensure_future(play(Data.media_instance))

        elif event == "_cat_search_btn" and Data.filename:
            if values["_cat_search_"]:
                Data.categories = get_categories(values["_cat_search_"])
                window["_table_countries_"].update(_rows(Data.categories))
            else:
                Data.categories = get_categories()
                window["_table_countries_"].update(_rows(Data.categories))

        elif event == "_ch_search_btn" and Data.filename:
            if values["_ch_search_"]:
                temp_list = []
                Data.selected_list = await generate_list(
                    values, Data.categories
                )
                for i, channel in enumerate(await get_selected()):
                    if values["_ch_search_"].lower() in channel[0].lower():
                        temp_list.append(Data.selected_list[i])
                Data.selected_list = temp_list
                window["_iptv_content_"].update(await get_selected())
            else:
                Data.selected_list = await generate_list(
                    values, Data.categories
                )
                window["_iptv_content_"].update(await get_selected())
        if event is not sg.TIMEOUT_KEY:
            if len(event) == 1:
                if ord(event) == 27:
                    Player.players.stop()


if __name__ == "__main__":
    asyncio.run(main())
