"""
ZedTV IPTV Player - Kivy Version
Modern UI with real thumbnail support
"""
from __version__ import FULL_VERSION_STRING, APP_AUTHOR, APP_YEAR

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, ObjectProperty
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Import existing logic
import sys
sys.path.insert(0, str(Path(__file__).parent))

from models import Data
from app import get_categories, get_selected, _rows
from thumbnails import get_thumbnail_path
from ui_settings import UISettings
from vlc_settings import VLCSettings
import player as vlc_player


class ChannelItem(RecycleDataViewBehavior, BoxLayout):
    """Widget for a single channel with thumbnail and info."""

    index = NumericProperty(0)
    title = StringProperty("")
    rating = StringProperty("")
    year = StringProperty("")
    logo_url = StringProperty("")
    is_selected = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 120
        self.padding = [5, 5]
        self.spacing = 10

        # Thumbnail
        self.thumbnail = AsyncImage(
            size_hint=(None, 1),
            width=100,
            allow_stretch=True,
            keep_ratio=True,
        )
        self.add_widget(self.thumbnail)

        # Info layout
        info_layout = BoxLayout(orientation='vertical', spacing=5)

        self.title_label = Label(
            text="",
            size_hint_y=0.5,
            font_size='16sp',
            halign='left',
            valign='middle',
            color=(1, 1, 1, 1),
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))

        self.info_label = Label(
            text="",
            size_hint_y=0.3,
            font_size='12sp',
            halign='left',
            valign='top',
            color=(0.8, 0.8, 0.8, 1),
        )
        self.info_label.bind(size=self.info_label.setter('text_size'))

        info_layout.add_widget(self.title_label)
        info_layout.add_widget(self.info_label)

        self.add_widget(info_layout)

        # Bind properties
        self.bind(
            title=self.update_labels,
            rating=self.update_labels,
            year=self.update_labels,
            logo_url=self.update_thumbnail,
        )

        # Background color
        with self.canvas.before:
            self.bg_color = Color(0.2, 0.2, 0.2, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        if self.is_selected:
            self.bg_color.rgba = (0.3, 0.4, 0.5, 1)
        else:
            self.bg_color.rgba = (0.2, 0.2, 0.2, 1)

    def update_labels(self, *args):
        self.title_label.text = self.title
        info_parts = []
        if self.rating:
            info_parts.append(f"⭐ {self.rating}")
        if self.year:
            info_parts.append(f"📅 {self.year}")
        self.info_label.text = " | ".join(info_parts)

    def update_thumbnail(self, *args):
        if self.logo_url:
            # Try to get cached thumbnail
            thumb_path = get_thumbnail_path(self.logo_url, 100)
            if thumb_path and Path(thumb_path).exists():
                self.thumbnail.source = thumb_path
            else:
                # Load from URL directly
                self.thumbnail.source = self.logo_url
        else:
            self.thumbnail.source = ""

    def refresh_view_attrs(self, rv, index, data):
        """Called by RecycleView to update this widget."""
        self.index = index
        super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Handle selection
            parent_rv = self.parent.parent.parent  # Get RecycleView
            if hasattr(parent_rv, 'select_channel'):
                parent_rv.select_channel(self.index)
            return True
        return super().on_touch_down(touch)


class ChannelRecycleView(RecycleView):
    """RecycleView for displaying channels with thumbnails."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.selected_index = -1

    def select_channel(self, index):
        """Select a channel."""
        self.selected_index = index
        # Update selection state
        for i, item in enumerate(self.data):
            item['is_selected'] = (i == index)
        self.refresh_from_data()

    def get_selected_index(self):
        return self.selected_index if self.selected_index >= 0 else None


class IPTVPlayerApp(App):
    """Main Kivy application."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ui_settings = UISettings()
        self.vlc_settings = VLCSettings()
        self.current_media = None

        # VLC player instance
        vlc_args = self.vlc_settings.get_vlc_args()
        self.vlc_instance = vlc_player.Instance(*vlc_args)
        self.vlc_player = self.vlc_instance.media_player_new()

    def build(self):
        """Build the UI."""
        Window.clearcolor = (0.1, 0.1, 0.1, 1)

        # Main layout
        main_layout = BoxLayout(orientation='vertical', spacing=5, padding=5)

        # Menu bar
        menu_bar = BoxLayout(size_hint_y=None, height=40, spacing=5)
        menu_bar.add_widget(Button(text="File", on_press=self.show_file_menu))
        menu_bar.add_widget(Button(text="Xtream", on_press=self.show_xtream_menu))
        menu_bar.add_widget(Button(text="Settings", on_press=self.show_settings_menu))
        menu_bar.add_widget(Button(text="About", on_press=self.show_about))
        main_layout.add_widget(menu_bar)

        # Content area (video + lists)
        content_layout = BoxLayout(orientation='horizontal', spacing=10)

        # Left side: Video player
        video_layout = BoxLayout(orientation='vertical')

        # Video canvas (placeholder for VLC)
        self.video_widget = Label(
            text="ZedTV IPTV Player\n\nSelect a channel to play",
            font_size='20sp',
            halign='center',
            valign='middle',
        )
        self.video_widget.canvas.before.clear()
        with self.video_widget.canvas.before:
            Color(0, 0, 0, 1)
            self.video_bg = Rectangle(size=self.video_widget.size, pos=self.video_widget.pos)
        self.video_widget.bind(
            size=lambda *args: setattr(self.video_bg, 'size', self.video_widget.size),
            pos=lambda *args: setattr(self.video_bg, 'pos', self.video_widget.pos)
        )

        video_layout.add_widget(self.video_widget)
        content_layout.add_widget(video_layout)

        # Right side: Categories + Channels
        lists_layout = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=10)

        # Categories
        cat_layout = BoxLayout(orientation='vertical', size_hint_y=0.5)
        cat_layout.add_widget(Label(text="Categories", size_hint_y=None, height=30, font_size='14sp'))

        self.category_search = TextInput(
            hint_text="Search categories...",
            size_hint_y=None,
            height=35,
            multiline=False,
        )
        self.category_search.bind(text=self.filter_categories)
        cat_layout.add_widget(self.category_search)

        self.category_list = GridLayout(cols=1, spacing=2, size_hint_y=None)
        self.category_list.bind(minimum_height=self.category_list.setter('height'))

        cat_scroll = ScrollView()
        cat_scroll.add_widget(self.category_list)
        cat_layout.add_widget(cat_scroll)

        lists_layout.add_widget(cat_layout)

        # Channels
        ch_layout = BoxLayout(orientation='vertical', size_hint_y=0.5)
        ch_layout.add_widget(Label(text="Channels", size_hint_y=None, height=30, font_size='14sp'))

        self.channel_search = TextInput(
            hint_text="Search channels...",
            size_hint_y=None,
            height=35,
            multiline=False,
        )
        self.channel_search.bind(text=self.filter_channels)
        ch_layout.add_widget(self.channel_search)

        # RecycleView for channels with thumbnails
        from kivy.uix.recycleboxlayout import RecycleBoxLayout

        self.channel_recycleview = ChannelRecycleView()
        self.channel_recycleview.viewclass = 'ChannelItem'

        # Set layout
        layout = RecycleBoxLayout(
            default_size=(None, 120),
            default_size_hint=(1, None),
            size_hint_y=None,
            orientation='vertical',
            spacing=2,
        )
        layout.bind(minimum_height=layout.setter('height'))
        self.channel_recycleview.add_widget(layout)

        ch_layout.add_widget(self.channel_recycleview)

        lists_layout.add_widget(ch_layout)

        content_layout.add_widget(lists_layout)

        main_layout.add_widget(content_layout)

        # Load initial data
        Clock.schedule_once(self.load_initial_data, 0.5)

        return main_layout

    def load_initial_data(self, dt):
        """Load initial categories."""
        Data.categories = get_categories()
        self.update_category_list()

    def update_category_list(self):
        """Update category list."""
        self.category_list.clear_widgets()
        for cat in Data.categories:
            btn = Button(
                text=cat,
                size_hint_y=None,
                height=40,
                on_press=lambda btn, c=cat: self.select_category(c)
            )
            self.category_list.add_widget(btn)

    def select_category(self, category):
        """Load channels for selected category."""
        print(f"Selected category: {category}")
        # This will be implemented with async data loading

    def filter_categories(self, instance, value):
        """Filter categories based on search."""
        # Implement filtering
        pass

    def filter_channels(self, instance, value):
        """Filter channels based on search."""
        # Implement filtering
        pass

    def show_file_menu(self, instance):
        """Show file menu."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        content.add_widget(Button(text="Open M3U File", on_press=self.open_file))
        content.add_widget(Button(text="Exit", on_press=self.stop))

        popup = Popup(title="File Menu", content=content, size_hint=(0.4, 0.3))
        popup.open()

    def show_xtream_menu(self, instance):
        """Show Xtream menu."""
        content = Label(text="Xtream menu - TBD")
        popup = Popup(title="Xtream", content=content, size_hint=(0.4, 0.3))
        popup.open()

    def show_settings_menu(self, instance):
        """Show settings menu."""
        content = Label(text="Settings - TBD")
        popup = Popup(title="Settings", content=content, size_hint=(0.4, 0.3))
        popup.open()

    def show_about(self, instance):
        """Show about dialog."""
        content = Label(text=f"{FULL_VERSION_STRING}\nKivy Edition\n\n{APP_AUTHOR} {APP_YEAR}")
        popup = Popup(title="About", content=content, size_hint=(0.4, 0.3))
        popup.open()

    def open_file(self, instance):
        """Open M3U file."""
        # File chooser will be implemented
        pass


if __name__ == '__main__':
    # Register custom widget
    from kivy.factory import Factory
    Factory.register('ChannelItem', ChannelItem)

    IPTVPlayerApp().run()

