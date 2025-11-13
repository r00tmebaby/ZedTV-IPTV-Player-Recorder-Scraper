"""
UI Settings Window for theme and font configuration
"""

from . import PySimpleGUI as sg
from core.ui_settings import UISettings, AVAILABLE_THEMES, AVAILABLE_FONTS, FONT_SIZES
from core.config import ICON


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

    # Build the layout with current font settings
    layout = [
        [sg.Text("UI Appearance Settings", font=(current_font, 14, "bold"))],
        [sg.HorizontalSeparator()],
        
        # Theme Selection
        [sg.Text("Color Theme", font=(current_font, 11, "bold"))],
        [
            sg.Text("Theme:", size=(20, 1), font=(current_font, current_font_size)),
            sg.Combo(
                AVAILABLE_THEMES,
                default_value=current_theme,
                key="_theme_",
                readonly=True,
                size=(25, 1),
                font=(current_font, current_font_size),
                enable_events=True,
            ),
            sg.Button("Preview", key="_preview_theme_", font=(current_font, current_button_size)),
        ],
        [sg.Text("Select a theme and click Preview to see how it looks", 
                 font=(current_font, 8), text_color="gray")],
        
        [sg.HorizontalSeparator()],
        
        # Font Settings
        [sg.Text("Font Settings", font=(current_font, 11, "bold"))],
        [
            sg.Text("Font Family:", size=(20, 1), font=(current_font, current_font_size)),
            sg.Combo(
                AVAILABLE_FONTS,
                default_value=current_font,
                key="_font_family_",
                readonly=True,
                size=(25, 1),
                font=(current_font, current_font_size),
            ),
        ],
        [sg.Text("Changes the font used throughout the application", 
                 font=(current_font, 8), text_color="gray")],
        
        [sg.HorizontalSeparator()],
        
        # Font Sizes
        [sg.Text("Font Sizes", font=(current_font, 11, "bold"))],
        [
            sg.Text("Normal Text:", size=(20, 1), font=(current_font, current_font_size)),
            sg.Combo(
                FONT_SIZES,
                default_value=current_font_size,
                key="_font_size_",
                readonly=True,
                size=(10, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text("(Default: 10)", font=(current_font, 8), text_color="gray"),
        ],
        [
            sg.Text("Titles:", size=(20, 1), font=(current_font, current_font_size)),
            sg.Combo(
                FONT_SIZES,
                default_value=current_title_size,
                key="_title_font_size_",
                readonly=True,
                size=(10, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text("(Default: 14)", font=(current_font, 8), text_color="gray"),
        ],
        [
            sg.Text("Buttons:", size=(20, 1), font=(current_font, current_font_size)),
            sg.Combo(
                FONT_SIZES,
                default_value=current_button_size,
                key="_button_font_size_",
                readonly=True,
                size=(10, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text("(Default: 10)", font=(current_font, 8), text_color="gray"),
        ],
        [
            sg.Text("Tables/Lists:", size=(20, 1), font=(current_font, current_font_size)),
            sg.Combo(
                FONT_SIZES,
                default_value=current_table_size,
                key="_table_font_size_",
                readonly=True,
                size=(10, 1),
                font=(current_font, current_font_size),
            ),
            sg.Text("(Default: 10)", font=(current_font, 8), text_color="gray"),
        ],
        
        [sg.HorizontalSeparator()],


        # Quick Presets
        [sg.Text("Quick Presets", font=(current_font, 11, "bold"))],
        [
            sg.Button("Small (9pt)", key="_preset_small_", font=(current_font, current_button_size)),
            sg.Button("Medium (10pt)", key="_preset_medium_", font=(current_font, current_button_size)),
            sg.Button("Large (12pt)", key="_preset_large_", font=(current_font, current_button_size)),
            sg.Button("Extra Large (14pt)", key="_preset_xlarge_", font=(current_font, current_button_size)),
        ],
        
        [sg.HorizontalSeparator()],
        
        # Buttons
        [
            sg.Button("Restore Defaults", key="_restore_defaults_", font=(current_font, current_button_size)),
            sg.Push(),
            sg.Button("Cancel", key="_cancel_", font=(current_font, current_button_size)),
            sg.Button("Save & Restart", key="_save_", button_color=("white", "green"), 
                     font=(current_font, current_button_size)),
        ],
        [sg.Text("Note: Changes require application restart to take full effect", 
                 font=(current_font, 9), text_color="orange")],
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
                    [sg.Listbox(["List Item 1", "List Item 2", "List Item 3"], size=(30, 3))],
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
                sg.popup_error(f"Could not preview theme: {e}", keep_on_top=True)
        
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
            from ui_settings import DEFAULT_UI_SETTINGS
            
            window["_theme_"].update(DEFAULT_UI_SETTINGS["theme"])
            window["_font_family_"].update(DEFAULT_UI_SETTINGS["font_family"])
            window["_font_size_"].update(DEFAULT_UI_SETTINGS["font_size"])
            window["_title_font_size_"].update(DEFAULT_UI_SETTINGS["title_font_size"])
            window["_button_font_size_"].update(DEFAULT_UI_SETTINGS["button_font_size"])
            window["_table_font_size_"].update(DEFAULT_UI_SETTINGS["table_font_size"])
            
            sg.popup("Settings restored to defaults\n\nClick 'Save & Restart' to apply.", 
                    keep_on_top=True)
        
        # Save settings
        elif event == "_save_":
            # Update settings
            current_settings.settings["theme"] = values["_theme_"]
            current_settings.settings["font_family"] = values["_font_family_"]
            current_settings.settings["font_size"] = values["_font_size_"]
            current_settings.settings["title_font_size"] = values["_title_font_size_"]
            current_settings.settings["button_font_size"] = values["_button_font_size_"]
            current_settings.settings["table_font_size"] = values["_table_font_size_"]
            
            
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

