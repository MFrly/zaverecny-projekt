# dialog_system.py
import pygame
import pygame_gui

from settings import *
from dialogues import NPC_DIALOGUES


class DialogSystem:
    """Správa NPC dialogu (E = začít, Enter = pokračovat)."""

    def __init__(self, manager: pygame_gui.UIManager):
        self.manager = manager

        self.active_dialogue = None
        self.dialog_index = 0
        self.current_npc = None

        self.dialog_box = None
        self.popup_active = False

    def is_active(self) -> bool:
        return self.popup_active

    def start_dialog(self, player, npc):
        self.popup_active = True
        player.set_input_enabled(False)

        self.current_npc = npc
        self.active_dialogue = NPC_DIALOGUES.get(npc.npc_id, [])

        # když NPC nemá dialog, nic neukazuj
        if not self.active_dialogue:
            self.end_dialog(player)
            return

        self.dialog_index = 0
        self._show_dialog_line()

    def start_custom_dialog(self, player, lines):
        """Spustí dialog z libovolného seznamu vět (ne z NPC_DIALOGUES)."""
        self.popup_active = True
        player.set_input_enabled(False)

        self.current_npc = None
        self.active_dialogue = list(lines) if lines else []

        if not self.active_dialogue:
            self.end_dialog(player)
            return

        self.dialog_index = 0
        self._show_dialog_line()


    def next_dialog(self, player):
        self.dialog_index += 1
        if not self.active_dialogue or self.dialog_index >= len(self.active_dialogue):
            self.end_dialog(player)
        else:
            self._show_dialog_line()

    def end_dialog(self, player):
        self.popup_active = False
        player.set_input_enabled(True)

        self.active_dialogue = None
        self.dialog_index = 0
        self.current_npc = None

        if self.dialog_box:
            self.dialog_box.kill()
            self.dialog_box = None

    def _show_dialog_line(self):
        if self.dialog_box:
            self.dialog_box.kill()
            self.dialog_box = None

        if not self.active_dialogue or self.dialog_index >= len(self.active_dialogue):
            return

        text = self.active_dialogue[self.dialog_index]
        self.dialog_box = pygame_gui.elements.UITextBox(
            text,
            pygame.Rect(WINDOW_WIDTH // 2 - 220, WINDOW_HEIGHT - 180, 440, 100),
            self.manager
        )
