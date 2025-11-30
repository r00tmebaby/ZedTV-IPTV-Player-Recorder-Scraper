"""
Settings Window for VLC configuration
"""

from core.config import ICON
from core.vlc_settings import (
    DEFAULT_VLC_SETTINGS,
    SETTING_DESCRIPTIONS,
    SETTING_OPTIONS,
    VLCSettings,
)
from ui import PySimpleGUI as sg


def _show_vlc_settings_window(current_settings: VLCSettings) -> bool:
    """
    Show VLC settings window.
    Returns True if settings were changed and VLC needs to be restarted.
    """

    # Tab 1: Network Settings
    network_tab = [
        [
            sg.Text(
                "Buffering & Caching",
                font=("Arial", 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text(
                "Network Buffer (ms):", size=(25, 1), pad=((10, 5), (5, 5))
            ),
            sg.Slider(
                range=(100, 5000),
                default_value=current_settings.settings["network_caching"],
                orientation="h",
                size=(30, 15),
                key="_network_caching_",
                enable_events=True,
            ),
            sg.Text(
                str(current_settings.settings["network_caching"]),
                key="_network_caching_display_",
                size=(6, 1),
                justification="right",
                pad=((5, 10), (5, 5)),
            ),
        ],
        [
            sg.Text(
                SETTING_DESCRIPTIONS["network_caching"],
                font=("Arial", 9),
                text_color="gray",
                pad=((10, 10), (0, 10)),
            )
        ],
        [
            sg.Text(
                "Live Stream Buffer (ms):", size=(25, 1), pad=((10, 5), (5, 5))
            ),
            sg.Slider(
                range=(50, 2000),
                default_value=current_settings.settings["live_caching"],
                orientation="h",
                size=(30, 15),
                key="_live_caching_",
                enable_events=True,
            ),
            sg.Text(
                str(current_settings.settings["live_caching"]),
                key="_live_caching_display_",
                size=(6, 1),
                justification="right",
                pad=((5, 10), (5, 5)),
            ),
        ],
        [
            sg.Text(
                SETTING_DESCRIPTIONS["live_caching"],
                font=("Arial", 9),
                text_color="gray",
                pad=((10, 10), (0, 20)),
            )
        ],
    ]

    # Tab 2: Video & Audio Settings
    video_audio_tab = [
        [
            sg.Text(
                "Video Settings",
                font=("Arial", 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text("Hardware Decoding:", size=(25, 1), pad=((10, 5), (5, 5))),
            sg.Combo(
                SETTING_OPTIONS["hw_decoding"],
                default_value=current_settings.settings["hw_decoding"],
                key="_hw_decoding_",
                readonly=True,
                size=(22, 1),
            ),
        ],
        [
            sg.Text(
                SETTING_DESCRIPTIONS["hw_decoding"],
                font=("Arial", 9),
                text_color="gray",
                pad=((10, 10), (0, 10)),
            )
        ],
        [
            sg.Text("Video Output:", size=(25, 1), pad=((10, 5), (5, 5))),
            sg.Combo(
                SETTING_OPTIONS["video_output"],
                default_value=current_settings.settings["video_output"],
                key="_video_output_",
                readonly=True,
                size=(22, 1),
            ),
        ],
        [
            sg.Text(
                SETTING_DESCRIPTIONS["video_output"],
                font=("Arial", 9),
                text_color="gray",
                pad=((10, 10), (0, 10)),
            )
        ],
        [
            sg.Text("Deinterlace:", size=(25, 1), pad=((10, 5), (5, 5))),
            sg.Combo(
                SETTING_OPTIONS["deinterlace"],
                default_value=current_settings.settings["deinterlace"],
                key="_deinterlace_",
                readonly=True,
                size=(22, 1),
            ),
        ],
        [
            sg.Text(
                SETTING_DESCRIPTIONS["deinterlace"],
                font=("Arial", 9),
                text_color="gray",
                pad=((10, 10), (0, 20)),
            )
        ],
        [sg.HorizontalSeparator(pad=((0, 0), (10, 10)))],
        [
            sg.Text(
                "Audio Settings",
                font=("Arial", 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text("Audio Output:", size=(25, 1), pad=((10, 5), (5, 5))),
            sg.Combo(
                SETTING_OPTIONS["audio_output"],
                default_value=current_settings.settings["audio_output"],
                key="_audio_output_",
                readonly=True,
                size=(22, 1),
            ),
        ],
        [
            sg.Text(
                SETTING_DESCRIPTIONS["audio_output"],
                font=("Arial", 9),
                text_color="gray",
                pad=((10, 10), (0, 10)),
            )
        ],
        [
            sg.Text(
                "Default Volume (%):", size=(25, 1), pad=((10, 5), (5, 5))
            ),
            sg.Slider(
                range=(0, 200),
                default_value=current_settings.settings["audio_volume"],
                orientation="h",
                size=(30, 15),
                key="_audio_volume_",
                enable_events=True,
            ),
            sg.Text(
                str(current_settings.settings["audio_volume"]),
                key="_audio_volume_display_",
                size=(6, 1),
                justification="right",
                pad=((5, 10), (5, 5)),
            ),
        ],
        [
            sg.Text(
                "Volume can be set above 100% for quiet streams",
                font=("Arial", 9),
                text_color="gray",
                pad=((10, 10), (0, 20)),
            )
        ],
    ]

    # Tab 3: Advanced Settings
    advanced_tab = [
        [
            sg.Text(
                "Performance Options",
                font=("Arial", 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Text(
                "These settings can improve playback on slower systems",
                font=("Arial", 9),
                text_color="gray",
                pad=((10, 10), (0, 15)),
            )
        ],
        [
            sg.Checkbox(
                "Skip frames if system is too slow",
                default=current_settings.settings["skip_frames"],
                key="_skip_frames_",
                pad=((10, 10), (5, 5)),
            ),
        ],
        [
            sg.Text(
                "Prevents audio/video desync on slow systems",
                font=("Arial", 9),
                text_color="gray",
                pad=((25, 10), (0, 10)),
            )
        ],
        [
            sg.Checkbox(
                "Drop frames that arrive too late",
                default=current_settings.settings["drop_late_frames"],
                key="_drop_late_frames_",
                pad=((10, 10), (5, 5)),
            ),
        ],
        [
            sg.Text(
                "Improves playback smoothness for network streams",
                font=("Arial", 9),
                text_color="gray",
                pad=((25, 10), (0, 10)),
            )
        ],
        [sg.HorizontalSeparator(pad=((0, 0), (15, 15)))],
        [
            sg.Text(
                "Maintenance",
                font=("Arial", 13, "bold"),
                pad=((5, 5), (10, 10)),
            )
        ],
        [
            sg.Checkbox(
                "Reset plugin cache on startup",
                default=current_settings.settings["reset_plugins_cache"],
                key="_reset_plugins_cache_",
                pad=((10, 10), (5, 5)),
            ),
        ],
        [
            sg.Text(
                "Clear VLC plugin cache to fix potential issues",
                font=("Arial", 9),
                text_color="gray",
                pad=((25, 10), (0, 20)),
            )
        ],
    ]

    # Build tabbed layout with improved spacing and organization
    layout = [
        [
            sg.Text(
                "VLC Player Settings",
                font=("Arial", 16, "bold"),
                pad=((10, 10), (10, 10)),
            )
        ],
        [
            sg.TabGroup(
                [
                    [
                        sg.Tab(
                            "Network",
                            network_tab,
                            key="_tab_network_",
                            font=("Arial", 10),
                        ),
                        sg.Tab(
                            "Video & Audio",
                            video_audio_tab,
                            key="_tab_video_audio_",
                            font=("Arial", 10),
                        ),
                        sg.Tab(
                            "Advanced",
                            advanced_tab,
                            key="_tab_advanced_",
                            font=("Arial", 10),
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
                size=(15, 1),
                pad=((10, 5), (5, 10)),
            ),
            sg.Push(),
            sg.Button(
                "Cancel", key="_cancel_", size=(10, 1), pad=((5, 5), (5, 10))
            ),
            sg.Button(
                "Save & Apply",
                key="_save_",
                button_color=("white", "green"),
                size=(12, 1),
                pad=((5, 10), (5, 10)),
            ),
        ],
        [
            sg.Text(
                "Note: Changes will be applied on next playback",
                font=("Arial", 9, "italic"),
                text_color="orange",
                pad=((10, 10), (0, 10)),
            )
        ],
    ]

    window = sg.Window(
        "VLC Settings",
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

        # Update slider displays
        if event == "_network_caching_":
            window["_network_caching_display_"].update(
                str(int(values["_network_caching_"]))
            )
        elif event == "_live_caching_":
            window["_live_caching_display_"].update(
                str(int(values["_live_caching_"]))
            )
        elif event == "_audio_volume_":
            window["_audio_volume_display_"].update(
                str(int(values["_audio_volume_"]))
            )

        # Restore defaults
        elif event == "_restore_defaults_":

            window["_network_caching_"].update(
                DEFAULT_VLC_SETTINGS["network_caching"]
            )
            window["_network_caching_display_"].update(
                str(DEFAULT_VLC_SETTINGS["network_caching"])
            )
            window["_live_caching_"].update(
                DEFAULT_VLC_SETTINGS["live_caching"]
            )
            window["_live_caching_display_"].update(
                str(DEFAULT_VLC_SETTINGS["live_caching"])
            )
            window["_hw_decoding_"].update(DEFAULT_VLC_SETTINGS["hw_decoding"])
            window["_audio_output_"].update(
                DEFAULT_VLC_SETTINGS["audio_output"]
            )
            window["_audio_volume_"].update(
                DEFAULT_VLC_SETTINGS["audio_volume"]
            )
            window["_audio_volume_display_"].update(
                str(DEFAULT_VLC_SETTINGS["audio_volume"])
            )
            window["_video_output_"].update(
                DEFAULT_VLC_SETTINGS["video_output"]
            )
            window["_deinterlace_"].update(DEFAULT_VLC_SETTINGS["deinterlace"])
            window["_skip_frames_"].update(DEFAULT_VLC_SETTINGS["skip_frames"])
            window["_drop_late_frames_"].update(
                DEFAULT_VLC_SETTINGS["drop_late_frames"]
            )
            window["_reset_plugins_cache_"].update(
                DEFAULT_VLC_SETTINGS["reset_plugins_cache"]
            )

            sg.popup("Settings restored to defaults", keep_on_top=True)

        # Save settings
        elif event == "_save_":
            # Update settings
            current_settings.settings["network_caching"] = int(
                values["_network_caching_"]
            )
            current_settings.settings["live_caching"] = int(
                values["_live_caching_"]
            )
            current_settings.settings["hw_decoding"] = values["_hw_decoding_"]
            current_settings.settings["audio_output"] = values[
                "_audio_output_"
            ]
            current_settings.settings["audio_volume"] = int(
                values["_audio_volume_"]
            )
            current_settings.settings["video_output"] = values[
                "_video_output_"
            ]
            current_settings.settings["deinterlace"] = values["_deinterlace_"]
            current_settings.settings["skip_frames"] = values["_skip_frames_"]
            current_settings.settings["drop_late_frames"] = values[
                "_drop_late_frames_"
            ]
            current_settings.settings["reset_plugins_cache"] = values[
                "_reset_plugins_cache_"
            ]

            # Save to file
            current_settings.save_settings()
            settings_changed = True

            sg.popup(
                "Settings saved!\n\nChanges will take effect on next playback.",
                keep_on_top=True,
            )
            break

    window.close()
    return settings_changed
