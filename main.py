import os
# إجبار النظام على استخدام ffpyplayer لتشغيل الفيديو من الإنترنت بنجاح
os.environ["KIVY_VIDEO"] = "ffpyplayer"

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.behaviors import FocusBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.network.urlrequest import UrlRequest
from kivy.core.window import Window
import xml.etree.ElementTree as ET
from datetime import datetime

Window.size = (1280, 720)

kv_design = """
#:import Window kivy.core.window.Window

<TVButton>:
    background_normal: ''
    background_color: (0, 0, 0, 0) if not self.focus else (1, 1, 1, 0.3)
    color: (1, 1, 1, 1)
    font_size: 24
    bold: True
    outline_width: 1
    outline_color: (0, 0, 0, 1)
    canvas.before:
        Color:
            rgba: (1, 1, 1, 1) if self.focus else (0, 0, 0, 0)
        Line:
            width: 2
            rectangle: self.x, self.y, self.width, self.height

FloatLayout:
    # خلفية سوداء تظهر أثناء التحميل
    canvas.before:
        Color:
            rgba: 0, 0, 0, 1
        Rectangle:
            pos: self.pos
            size: self.size

    # رسالة التحميل (تظهر فقط عندما يكون الفيديو غير جاهز)
    Label:
        text: 'Diffusion en cours...'
        font_size: 45
        bold: True
        color: 1, 1, 1, 1
        opacity: 1 if not video_player.loaded else 0

    # 1. خلفية الفيديو
    Video:
        id: video_player
        source: 'https://treso.ma/load/vids/intro1.mp4'
        state: 'play'
        options: {'eos': 'loop'}
        allow_stretch: True
        keep_ratio: False
        size_hint: 1, 1
        # إخفاء الفيديو حتى يكتمل تحميله
        opacity: 1 if self.loaded else 0

    # 2. القائمة المنسدلة (شفافة بالكامل)
    BoxLayout:
        orientation: 'vertical'
        size_hint: 0.25, None
        height: self.minimum_height
        pos_hint: {'top': 0.98, 'x': 0.02}
        
        TVButton:
            id: main_menu_btn
            text: 'Chaines [+]'
            size_hint_y: None
            height: 60
            on_release: app.toggle_menu()
        
        ScrollView:
            id: dropdown_scroll
            size_hint_y: None
            height: 0
            opacity: 0
            canvas.before:
                Color:
                    rgba: 0, 0, 0, 0 
                Rectangle:
                    pos: self.pos
                    size: self.size
            BoxLayout:
                id: dropdown_menu
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 2

    # 3. الشريط السفلي (الأخبار + التوقيت)
    BoxLayout:
        size_hint: 1, 0.08
        pos_hint: {'y': 0}
        
        FloatLayout:
            id: ticker_container
            canvas.before:
                Color:
                    rgba: 0.5, 0.0, 0.0, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            
            StencilView:
                pos_hint: {'x': 0, 'y': 0}
                size_hint: 1, 1
                Label:
                    id: news_label
                    text: 'Chargement des actualites...'
                    color: 1, 1, 1, 1
                    font_size: 26
                    size_hint_x: None
                    width: self.texture_size[0]

        Label:
            id: clock_label
            text: '00:00:00'
            size_hint_x: 0.15
            font_size: 30
            bold: True
            color: 0, 0, 0, 1
            canvas.before:
                Color:
                    rgba: 0.8, 0.7, 0.0, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
"""

class TVButton(FocusBehavior, Button):
    pass

class TVApp(App):
    def build(self):
        self.root = Builder.load_string(kv_design)
        self.setup_menu()
        self.fetch_news()
        Clock.schedule_interval(self.update_clock, 1)
        return self.root

    def setup_menu(self):
        menu = self.root.ids.dropdown_menu
        for i in range(1, 13):
            btn = TVButton(text=f'Canal {i}', size_hint_y=None, height=50)
            btn.bind(on_release=lambda instance: self.hide_menu())
            menu.add_widget(btn)

    def toggle_menu(self):
        scroll = self.root.ids.dropdown_scroll
        if scroll.height == 0:
            scroll.height = 350
            scroll.opacity = 1
        else:
            self.hide_menu()

    def hide_menu(self):
        scroll = self.root.ids.dropdown_scroll
        scroll.height = 0
        scroll.opacity = 0

    def update_clock(self, dt):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.root.ids.clock_label.text = current_time

    def fetch_news(self):
        url = "https://www.france24.com/fr/rss"
        UrlRequest(url, on_success=self.on_news_success, on_error=self.on_news_error, on_failure=self.on_news_error)

    def on_news_success(self, request, result):
        try:
            root = ET.fromstring(result)
            titles = []
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text
                # تنظيف النص من الرموز المعقدة التي تظهر كعلامة X في Kivy
                title = title.replace('’', "'").replace('‘', "'").replace('«', '"').replace('»', '"').replace('\xa0', ' ').replace('\u2013', '-')
                titles.append(title)
            
            news_text = "   ---   ".join(titles) + "   ---   "
        except Exception:
            news_text = "Erreur lors du chargement des actualites...   ---   "
        self.start_ticker(news_text)

    def on_news_error(self, request, error):
        fallback_news = "Urgent: Lancement de l'application Smart TV   ---   Technologie: Kivy offre d'excellentes solutions   ---   "
        self.start_ticker(fallback_news)

    def start_ticker(self, text):
        label = self.root.ids.news_label
        label.text = text
        label.texture_update()
        
        container_width = Window.width
        text_width = label.texture_size[0]
        
        label.x = container_width
        duration = (text_width + container_width) / 90.0
        
        anim = Animation(x=-text_width, duration=duration)
        anim.bind(on_complete=self.restart_ticker)
        anim.start(label)

    def restart_ticker(self, animation, widget):
        self.start_ticker(widget.text)

if __name__ == '__main__':
    TVApp().run()