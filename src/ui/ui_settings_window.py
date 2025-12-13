"""
UI Settings Window for theme and font configuration
"""

from core.config import ICON
from core.ui_settings import (
    AVAILABLE_FONTS,
    AVAILABLE_THEMES,
    DEFAULT_UI_SETTINGS,
    FONT_SIZES,
    UISettings,
)

from . import PySimpleGUI as sg


def _show_ui_settings_window(current_settings: UISettings) -> bool:
    """
    Show UI settings window for theme and font customization.
    Returns True if settings were changed and app needs to be restarted.
    """

    # Get current values
    current_theme = current_settings.settings.get("theme", "DarkTeal6")
    current_font = current_settings.settings.get("font_family", "Arial")
    current_font_size = current_settings.settings.get("font_size", 10)
    current_title_size = current_settings.settings.get("title_font_size", 14)
    current_button_size = current_settings.settings.get("button_font_size", 10)
    current_table_size = current_settings.settings.get("table_font_size", 10)

    # Tab 1: Theme Settings
    theme_tab = [
        [
            sg.Text(
                "Color Theme",
                font=(current_font, 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text(
                "Theme:",
                size=(18, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Combo(
                AVAILABLE_THEMES,
                default_value=current_theme,
                key="_theme_",
                readonly=True,
                size=(28, 1),
                font=(current_font, current_font_size),
                enable_events=True,
            ),
            sg.Button(
                "Preview",
                key="_preview_theme_",
                font=(current_font, current_button_size),
                size=(10, 1),
            ),
        ],
        [
            sg.Text(
                "Select a theme and click Preview to see how it looks",
                font=(current_font, 9),
                text_color="gray",
                pad=((10, 10), (0, 20)),
            )
        ],
    ]

    # Tab 2: Font Settings
    font_tab = [
        [
            sg.Text(
                "Font Family",
                font=(current_font, 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text(
                "Font Family:",
                size=(18, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Combo(
                AVAILABLE_FONTS,
                default_value=current_font,
                key="_font_family_",
                readonly=True,
                size=(28, 1),
                font=(current_font, current_font_size),
            ),
        ],
        [
            sg.Text(
                "Changes the font used throughout the application",
                font=(current_font, 9),
                text_color="gray",
                pad=((10, 10), (0, 20)),
            )
        ],
        [sg.HorizontalSeparator(pad=((0, 0), (10, 10)))],
        [
            sg.Text(
                "Font Sizes",
                font=(current_font, 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text(
                "Normal Text:",
                size=(18, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Combo(
                FONT_SIZES,
                default_value=current_font_size,
                key="_font_size_",
                readonly=True,
                size=(12, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text(
                "(Default: 10)", font=(current_font, 9), text_color="gray"
            ),
        ],
        [
            sg.Text(
                "Titles:",
                size=(18, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Combo(
                FONT_SIZES,
                default_value=current_title_size,
                key="_title_font_size_",
                readonly=True,
                size=(12, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text(
                "(Default: 14)", font=(current_font, 9), text_color="gray"
            ),
        ],
        [
            sg.Text(
                "Buttons:",
                size=(18, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Combo(
                FONT_SIZES,
                default_value=current_button_size,
                key="_button_font_size_",
                readonly=True,
                size=(12, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text(
                "(Default: 10)", font=(current_font, 9), text_color="gray"
            ),
        ],
        [
            sg.Text(
                "Tables/Lists:",
                size=(18, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Combo(
                FONT_SIZES,
                default_value=current_table_size,
                key="_table_font_size_",
                readonly=True,
                size=(12, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text(
                "(Default: 10)",
                font=(current_font, 9),
                text_color="gray",
                pad=((5, 10), (5, 5)),
            ),
        ],
    ]

    # Tab 3: Keyboard Shortcuts
    current_key_exit_fullscreen = current_settings.settings.get("key_exit_fullscreen", "Escape")
    current_key_toggle_controls = current_settings.settings.get("key_toggle_controls", "c")
    current_key_play_pause = current_settings.settings.get("key_play_pause", "space")
    current_key_fullscreen = current_settings.settings.get("key_fullscreen", "f")

    keyboard_tab = [
        [
            sg.Text(
                "Keyboard Shortcuts",
                font=(current_font, 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text(
                "Customize keyboard shortcuts for common actions",
                font=(current_font, 9),
                text_color="gray",
                pad=((10, 10), (0, 15)),
            )
        ],
        [
            sg.Text(
                "Exit Fullscreen:",
                size=(20, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Input(
                current_key_exit_fullscreen,
                key="_key_exit_fullscreen_",
                size=(20, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text(
                "Default: Escape",
                font=(current_font, 9),
                text_color="gray",
            ),
        ],
        [
            sg.Text(
                "Toggle Controls:",
                size=(20, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Input(
                current_key_toggle_controls,
                key="_key_toggle_controls_",
                size=(20, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text(
                "Default: c",
                font=(current_font, 9),
                text_color="gray",
            ),
        ],
        [
            sg.Text(
                "Play/Pause:",
                size=(20, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Input(
                current_key_play_pause,
                key="_key_play_pause_",
                size=(20, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text(
                "Default: space",
                font=(current_font, 9),
                text_color="gray",
            ),
        ],
        [
            sg.Text(
                "Toggle Fullscreen:",
                size=(20, 1),
                font=(current_font, current_font_size),
                pad=((10, 10), (5, 5)),
            ),
            sg.Input(
                current_key_fullscreen,
                key="_key_fullscreen_",
                size=(20, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text(
                "Default: f",
                font=(current_font, 9),
                text_color="gray",
            ),
        ],
        [sg.HorizontalSeparator(pad=((0, 0), (10, 10)))],
        [
            sg.Text(
                "Common Key Names:",
                font=(current_font, 11, "bold"),
                pad=((10, 10), (5, 5)),
            ),
        ],
        [
            sg.Text(
                "Letters: a-z, A-Z\n"
                "Numbers: 0-9\n"
                "Special: Escape, Return, space, Tab\n"
                "Arrows: Up, Down, Left, Right\n"
                "Function: F1-F12\n"
                "Modifiers: Control_L, Alt_L, Shift_L",
                font=(current_font, 9),
                text_color="gray",
                pad=((10, 10), (5, 10)),
            ),
        ],
    ]

    # Tab 4: Quick Presets
    presets_tab = [
        [
            sg.Text(
                "Quick Font Presets",
                font=(current_font, 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text(
                "Apply predefined font size combinations for different preferences",
                font=(current_font, 9),
                text_color="gray",
                pad=((10, 10), (0, 15)),
            )
        ],
        [
            sg.Button(
                "Small (9pt)",
                key="_preset_small_",
                font=(current_font, current_button_size),
                size=(20, 2),
                pad=((10, 5), (5, 5)),
            ),
            sg.Text(
                "Compact interface\nBest for high-resolution displays",
                font=(current_font, 9),
                text_color="gray",
                justification="left",
            ),
        ],
        [
            sg.Button(
                "Medium (10pt)",
                key="_preset_medium_",
                font=(current_font, current_button_size),
                size=(20, 2),
                pad=((10, 5), (5, 5)),
            ),
            sg.Text(
                "Default settings\nBalanced for most users",
                font=(current_font, 9),
                text_color="gray",
                justification="left",
            ),
        ],
        [
            sg.Button(
                "Large (12pt)",
                key="_preset_large_",
                font=(current_font, current_button_size),
                size=(20, 2),
                pad=((10, 5), (5, 5)),
            ),
            sg.Text(
                "Comfortable reading\nGood for accessibility",
                font=(current_font, 9),
                text_color="gray",
                justification="left",
            ),
        ],
        [
            sg.Button(
                "Extra Large (14pt)",
                key="_preset_xlarge_",
                font=(current_font, current_button_size),
                size=(20, 2),
                pad=((10, 5), (5, 5)),
            ),
            sg.Text(
                "Maximum readability\nIdeal for large screens",
                font=(current_font, 9),
                text_color="gray",
                justification="left",
            ),
        ],
    ]

    # Build tabbed layout
    layout = [
        [
            sg.Text(
                "UI Appearance Settings",
                font=(current_font, 16, "bold"),
                pad=((10, 10), (10, 10)),
            )
        ],
        [
            sg.TabGroup(
                [
                    [
                        sg.Tab(
                            "Theme",
                            theme_tab,
                            key="_tab_theme_",
                            font=(current_font, 10),
                        ),
                        sg.Tab(
                            "Fonts",
                            font_tab,
                            key="_tab_fonts_",
                            font=(current_font, 10),
                        ),
                        sg.Tab(
                            "Keyboard",
                            keyboard_tab,
                            key="_tab_keyboard_",
                            font=(current_font, 10),
                        ),
                        sg.Tab(
                            "Presets",
                            presets_tab,
                            key="_tab_presets_",
                            font=(current_font, 10),
                        ),
                    ]
                ],
                pad=((5, 5), (5, 15)),
                expand_x=True,
                expand_y=True,
            )
        ],
        [sg.HorizontalSeparator(pad=((0, 0), (5, 10)))],
        # Action Buttons - Right aligned with proper spacing
        [
            sg.Button(
                "Restore Defaults",
                key="_restore_defaults_",
                font=(current_font, current_button_size),
                size=(15, 1),
                pad=((10, 5), (5, 10)),
            ),
            sg.Push(),
            sg.Button(
                "Cancel",
                key="_cancel_",
                font=(current_font, current_button_size),
                size=(10, 1),
                pad=((5, 5), (5, 10)),
            ),
            sg.Button(
                "Save & Restart",
                key="_save_",
                button_color=("white", "green"),
                font=(current_font, current_button_size),
                size=(13, 1),
                pad=((5, 10), (5, 10)),
            ),
        ],
        [
            sg.Text(
                "Note: Changes require application restart to take full effect",
                font=(current_font, 9, "italic"),
                text_color="orange",
                pad=((10, 10), (0, 10)),
            )
        ],
    ]

    window = sg.Window(
        "UI Settings",
        layout,
        icon=ICON,
        modal=True,
        finalize=True,
    )

    settings_changed = False

    while True:
        event, values = window.read()

        if event in (sg.WIN_CLOSED, "_cancel_"):
            break

        # Preview theme
        elif event == "_preview_theme_":
            preview_theme = values["_theme_"]
            try:
                # Create a small preview window
                sg.theme(preview_theme)
                preview_layout = [
                    [sg.Text("Theme Preview", font=("Arial", 14, "bold"))],
                    [sg.Text(f"Current Theme: {preview_theme}")],
                    [sg.Button("Button Example"), sg.Input("Input Example")],
                    [
                        sg.Listbox(
                            ["List Item 1", "List Item 2", "List Item 3"],
                            size=(30, 3),
                        )
                    ],
                    [sg.OK()],
                ]
                preview_win = sg.Window(
                    f"Preview: {preview_theme}",
                    preview_layout,
                    modal=True,
                )
                preview_win.read()
                preview_win.close()
                # Restore current theme
                sg.theme(current_theme)
            except Exception as e:
                sg.popup_error(
                    f"Could not preview theme: {e}", keep_on_top=True
                )

        # Presets
        elif event == "_preset_small_":
            window["_font_size_"].update(9)
            window["_title_font_size_"].update(12)
            window["_button_font_size_"].update(9)
            window["_table_font_size_"].update(9)

        elif event == "_preset_medium_":
            window["_font_size_"].update(10)
            window["_title_font_size_"].update(14)
            window["_button_font_size_"].update(10)
            window["_table_font_size_"].update(10)

        elif event == "_preset_large_":
            window["_font_size_"].update(12)
            window["_title_font_size_"].update(16)
            window["_button_font_size_"].update(12)
            window["_table_font_size_"].update(12)

        elif event == "_preset_xlarge_":
            window["_font_size_"].update(14)
            window["_title_font_size_"].update(18)
            window["_button_font_size_"].update(14)
            window["_table_font_size_"].update(14)

        # Restore defaults
        elif event == "_restore_defaults_":

            window["_theme_"].update(DEFAULT_UI_SETTINGS["theme"])
            window["_font_family_"].update(DEFAULT_UI_SETTINGS["font_family"])
            window["_font_size_"].update(DEFAULT_UI_SETTINGS["font_size"])
            window["_title_font_size_"].update(
                DEFAULT_UI_SETTINGS["title_font_size"]
            )
            window["_button_font_size_"].update(
                DEFAULT_UI_SETTINGS["button_font_size"]
            )
            window["_table_font_size_"].update(
                DEFAULT_UI_SETTINGS["table_font_size"]
            )
            window["_key_exit_fullscreen_"].update(
                DEFAULT_UI_SETTINGS["key_exit_fullscreen"]
            )
            window["_key_toggle_controls_"].update(
                DEFAULT_UI_SETTINGS["key_toggle_controls"]
            )
            window["_key_play_pause_"].update(
                DEFAULT_UI_SETTINGS["key_play_pause"]
            )
            window["_key_fullscreen_"].update(
                DEFAULT_UI_SETTINGS["key_fullscreen"]
            )

            sg.popup(
                "Settings restored to defaults\n\nClick 'Save & Restart' to apply.",
                keep_on_top=True,
            )

        # Save settings
        elif event == "_save_":
            # Update settings
            current_settings.settings["theme"] = values["_theme_"]
            current_settings.settings["font_family"] = values["_font_family_"]
            current_settings.settings["font_size"] = values["_font_size_"]
            current_settings.settings["title_font_size"] = values[
                "_title_font_size_"
            ]
            current_settings.settings["key_exit_fullscreen"] = values[
                "_key_exit_fullscreen_"
            ]
            current_settings.settings["key_toggle_controls"] = values[
                "_key_toggle_controls_"
            ]
            current_settings.settings["key_play_pause"] = values[
                "_key_play_pause_"
            ]
            current_settings.settings["key_fullscreen"] = values[
                "_key_fullscreen_"
            ]
            current_settings.settings["button_font_size"] = values[
                "_button_font_size_"
            ]
            current_settings.settings["table_font_size"] = values[
                "_table_font_size_"
            ]

            # Save to file
            current_settings.save_settings()
            settings_changed = True

            sg.popup(
                "UI settings saved!\n\n"
                "Please restart the application for changes to take full effect.\n\n"
                "The application will now close.",
                title="Settings Saved",
                keep_on_top=True,
            )
            break

    window.close()
    return settings_changed
