import PySimpleGUI as sg
from models import Data
from app import _rows

menu_def = [
    ["&File", ["&Open", "&Custom List", "&Exit"]],
    ["&Xtream", ["&Add Account", "&Accounts...", "&Reload from Current"]],
    ["&Settings", ["&IP Info"]],
    ["&Help", "&About"],
]

layout = [
    [
        sg.Col(
            [
                [sg.Menu(menu_def, tearoff=False, pad=(200, 1))],
                [
                    sg.Col(
                        [
                            [
                                sg.Canvas(
                                    key="_canvas_video_",
                                    background_color="black",
                                    expand_x=True,
                                    expand_y=True,
                                    size=(750, 450),
                                    pad=(5, 5),
                                )
                            ]
                        ],
                        expand_x=True,
                        key="_tests_",
                        expand_y=True,
                    )
                ],
                [
                    sg.Col(
                        [
                            [
                                sg.I(key="_cat_search_", expand_x=True),
                                sg.B(
                                    "Search",
                                    key="_cat_search_btn",
                                    size=(5, 1),
                                    pad=(5, 5),
                                ),
                            ],
                            [
                                sg.Table(
                                    values=_rows(Data.categories),
                                    headings=["Category"],
                                    key="_table_countries_",
                                    change_submits=True,
                                    expand_y=True,
                                    expand_x=True,
                                    justification="l",
                                    size=(200, 500),
                                )
                            ],
                        ],
                        expand_x=True,
                        expand_y=True,
                    ),
                    sg.Col(
                        [
                            [
                                sg.I(key="_ch_search_", expand_x=True),
                                sg.B(
                                    "Search",
                                    key="_ch_search_btn",
                                    pad=(5, 5),
                                    size=(5, 1),
                                ),
                            ],
                            [
                                sg.Table(
                                    values=[[" "]],
                                    headings=[
                                        "Title                        ",
                                        "Rating",
                                        "Year",
                                    ],
                                    key="_iptv_content_",
                                    justification="l",
                                    expand_y=True,
                                    expand_x=True,
                                    right_click_menu=[
                                        "&Menu",
                                        [
                                            "&Full Screen",
                                            "&Record",
                                            "&Play in VLC",
                                            "&Stop"
                                        ],
                                    ],
                                    bind_return_key=True,
                                    enable_click_events=True,
                                    size=(200, 500),
                                ),
                            ],
                        ],
                        expand_x=True,
                        expand_y=True,
                    ),
                ],
            ],
            expand_x=True,
            expand_y=True,
        )
    ]
]
