# main.py
# Application CENAD — Point d'entrée avec Drawer latéral animé (remplace Popup)
import os
import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Config Kivy avant tout import
os.environ.setdefault('KIVY_NO_ENV_CONFIG', '1')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.modalview import ModalView
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

import data.database as db
from ui.themes import ThemeManager
from ui.widgets import MenuButton

from ui.screens import (
    AccueilScreen,
    MembresScreen,
    MembreDetailScreen,
    PresidentsScreen,
    PresidentDetailScreen,
    EtablissementsScreen,
    EtabDetailScreen,
    BatimentsScreen,
    HistoriqueScreen,
    ParametresScreen,
    AProposScreen,
    BaseScreen,
    ParametresScreen,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Drawer latéral animé (ModalView)
# ──────────────────────────────────────────────

class Drawer(ModalView):
    """
    Drawer latéral animé.
    - Fournit overlay sombre via ModalView
    - Panel glissant depuis la gauche (animé sur x)
    - Items construits avec MenuButton (icône + texte)
    - Ferme au clic extérieur ou à la sélection d'un item
    """
    def __init__(self, nav_items, navigate_fn, width_dp=260, **kwargs):
        super().__init__(auto_dismiss=False, background_color=(0, 0, 0, 0.45), **kwargs)
        self._w = dp(width_dp)
        # ModalView occupe toute la fenêtre ; on aligne notre panel à gauche
        self.size_hint = (None, 1)
        self.width = Window.width
        self._navigate = navigate_fn
        self.nav_items = nav_items

        # Root horizontal : panel gauche + spacer droit
        root = BoxLayout(orientation='horizontal', size_hint=(None, 1), width=self.width)

        # Panel drawer (left)
        self.panel = BoxLayout(orientation='vertical', size_hint=(None, 1), width=self._w)
        with self.panel.canvas.before:
            Color(*ThemeManager.color('surface'))
            self._panel_bg = Rectangle(pos=self.panel.pos, size=self.panel.size)
        self.panel.bind(pos=lambda *_: setattr(self._panel_bg, 'pos', self.panel.pos),
                        size=lambda *_: setattr(self._panel_bg, 'size', self.panel.size))

        # Header
        header = BoxLayout(size_hint_y=None, height=dp(84), padding=[dp(16), dp(12)])
        header.add_widget(Label(text='[b]CENAD[/b]\nNavigation', markup=True,
                                color=ThemeManager.color('primary'), halign='left', valign='middle'))
        self.panel.add_widget(header)

        # Items (scrollable)
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView()
        items_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(2))
        items_box.bind(minimum_height=items_box.setter('height'))

        for icon_name, label, screen in self.nav_items:
            btn = MenuButton(text=label, icon_name=icon_name, on_press_fn=lambda *a, s=screen: self._on_select(s))
            btn.size_hint_y = None
            btn.height = dp(52)
            items_box.add_widget(btn)

        scroll.add_widget(items_box)
        self.panel.add_widget(scroll)

        # Spacer to capture outside clicks
        spacer = BoxLayout()
        root.add_widget(self.panel)
        root.add_widget(spacer)
        self.add_widget(root)

        # Start off-screen
        self.panel.x = -self._w

    def open(self, *largs):
        super().open(*largs)
        Animation.cancel_all(self.panel)
        Animation(x=0, d=0.22, t='out_quad').start(self.panel)

    def dismiss(self, *largs, **kwargs):
        def _do_dismiss(*_):
            super(Drawer, self).dismiss(*largs, **kwargs)
        Animation.cancel_all(self.panel)
        anim = Animation(x=-self._w, d=0.18, t='in_quad')
        anim.bind(on_complete=lambda *_: _do_dismiss())
        anim.start(self.panel)

    def _on_select(self, screen_name):
        self.dismiss()
        try:
            self._navigate(screen_name)
        except Exception:
            pass

    def on_touch_down(self, touch):
        # If touch outside panel, close drawer
        if not self.panel.collide_point(*touch.pos):
            self.dismiss()
            return True
        return super().on_touch_down(touch)


# ──────────────────────────────────────────────
# Barre supérieure
# ──────────────────────────────────────────────

class TopBar(BoxLayout):
    """Barre de navigation supérieure avec bouton hamburger iconé et titre."""

    def __init__(self, on_menu_toggle, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(54),
            spacing=dp(8),
            padding=[dp(6), dp(6)],
            **kwargs
        )
        self._on_toggle = on_menu_toggle
        self._draw_bg()

        # Bouton hamburger (utilise MenuButton pour icône + style)
        self.ham = MenuButton(text='', icon_name='menu', on_press_fn=lambda *a: self._on_toggle())
        self.ham.size_hint = (None, 1)
        self.ham.width = dp(48)
        self.add_widget(self.ham)

        # Titre
        self.title = Label(
            text='[b]CENAD[/b]',
            markup=True,
            color=ThemeManager.color('text'),
            font_size='17sp',
            halign='left',
            valign='middle',
        )
        self.title.bind(size=self.title.setter('text_size'))
        self.add_widget(self.title)

    def _draw_bg(self):
        with self.canvas.before:
            Color(*ThemeManager.color('surface'))
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(
            pos=lambda *a: setattr(self._bg, 'pos', self.pos),
            size=lambda *a: setattr(self._bg, 'size', self.size),
        )

    def set_title(self, text):
        self.title.text = f'[b]{text}[/b]'


# ──────────────────────────────────────────────
# Application principale (topbar + ScreenManager + Drawer)
# ──────────────────────────────────────────────

class CENADApp(App):
    title = 'CENAD – Annuaire UNA'

    # État partagé entre écrans
    current_membre    = None
    current_president = None
    current_etab      = None

    # Navigation principale (icônes attendues dans assets/images/icones)
    NAV_ITEMS = [
        ('home',      'Accueil',        'accueil'),
        ('group',      'Membres',        'membres'),
        ('building',   'Établissements', 'etablissements'),
        ('crown',      'Présidents',     'presidents'),
        ('location',   'Bâtiments',      'batiments'),
        ('scroll',     'Historique',     'historique'),
        ('settings',   'Paramètres',     'parametres'),
        ('info',       'À propos',       'apropos'),
    ]

    def build(self):
        # Initialisation base de données
        db.init_database()

        # Appliquer thème sauvegardé
        ThemeManager.apply(db.get_setting('theme', 'dark'))

        # Racine : colonne verticale (topbar + contenu)
        self.root_box = BoxLayout(orientation='vertical')

        # Topbar
        self.top_bar = TopBar(on_menu_toggle=self._toggle_menu)
        self.root_box.add_widget(self.top_bar)

        # ScreenManager
        self.sm = ScreenManager(transition=SlideTransition(duration=0.18))
        self._register_screens()
        self.root_box.add_widget(self.sm)

        # Drawer placeholder (instancié à la demande)
        self._drawer = None

        return self.root_box

    def _register_screens(self):
        """Instancie tous les écrans et les ajoute au ScreenManager."""
        for screen in [
            AccueilScreen(app=self),
            MembresScreen(app=self),
            MembreDetailScreen(app=self),
            PresidentsScreen(app=self),
            PresidentDetailScreen(app=self),
            EtablissementsScreen(app=self),
            EtabDetailScreen(app=self),
            BatimentsScreen(app=self),
            HistoriqueScreen(app=self),
            ParametresScreen(app=self),
            AProposScreen(app=self),
        ]:
            self.sm.add_widget(screen)
        self.sm.current = 'accueil'

    def go_to(self, screen_name: str):
        """Navigation vers un écran par son nom et mise à jour du titre."""
        if self.sm.has_screen(screen_name):
            self.sm.current = screen_name
            titles = {
                'accueil':          'CENAD',
                'membres':          'Annuaire',
                'membre_detail':    'Membre',
                'presidents':       'Présidents',
                'president_detail': 'Président',
                'etablissements':   'Établissements',
                'etab_detail':      'Établissement',
                'batiments':        'Bâtiments',
                'historique':       'Historique',
                'parametres':       'Paramètres',
                'apropos':          'À propos',
            }
            self.top_bar.set_title(titles.get(screen_name, screen_name))
        else:
            logger.warning(f"Écran inconnu : {screen_name}")

    def _toggle_menu(self):
        """Ouvre le Drawer latéral animé (ou le ferme s'il est ouvert)."""
        # Si drawer déjà ouvert, on le ferme
        if getattr(self, '_drawer', None) and getattr(self._drawer, '_window', None):
            try:
                self._drawer.dismiss()
            except Exception:
                pass
            return

        # Construire et ouvrir le drawer
        self._drawer = Drawer(nav_items=self.NAV_ITEMS, navigate_fn=self.go_to, width_dp=260)
        self._drawer.open()

    # Compatibilité : méthode publique pour ouvrir le menu depuis écrans si besoin
    def open_menu(self):
        self._toggle_menu()


# ──────────────────────────────────────────────
# Lancement
# ──────────────────────────────────────────────

if __name__ == '__main__':
    CENADApp().run()

