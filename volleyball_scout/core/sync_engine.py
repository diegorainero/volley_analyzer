"""
Volleyball Scout - Sync Engine
Collega i timestamp video agli eventi di scouting
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Callable
from threading import Thread, Event as ThreadEvent

logger = logging.getLogger(__name__)


@dataclass
class SyncState:
    """Stato corrente del sync video↔scouting"""
    video_position: float = 0.0      # secondi dall'inizio video
    video_offset:   float = 0.0      # offset calibrazione
    is_playing:     bool  = False
    rally_number:   int   = 1
    set_number:     int   = 1
    score_home:     int   = 0
    score_away:     int   = 0

    @property
    def match_time(self) -> float:
        """Tempo partita = posizione video - offset"""
        return max(0.0, self.video_position - self.video_offset)


class SyncEngine:
    """
    Motore di sincronizzazione video↔eventi.
    
    Funzionamento:
    - Il player video aggiorna video_position ogni frame (~40ms)
    - Quando lo scout inserisce un evento, il timestamp è video_position
    - L'offset permette di allineare inizio video con inizio partita
    """

    def __init__(self):
        self.state = SyncState()
        self._callbacks: list[Callable[[SyncState], None]] = []
        self._position_thread: Thread | None = None
        self._stop_event = ThreadEvent()

        # Hook da collegare al player VLC
        self.player_get_time: Callable[[], float] | None = None

    # ──────────────────────────────────
    #  Calibrazione offset
    # ──────────────────────────────────

    def calibrate_offset(self, video_pos: float):
        """
        Imposta l'offset: chiama questo al fischio d'inizio
        video_pos = posizione corrente del video in quel momento
        """
        self.state.video_offset = video_pos
        logger.info("📍 Offset calibrato: %.2f s", video_pos)
        self._notify()

    def set_offset_manual(self, offset_seconds: float):
        """Imposta offset manuale (recuperato da DB per match salvati)"""
        self.state.video_offset = offset_seconds
        self._notify()

    # ──────────────────────────────────
    #  Aggiornamento posizione
    # ──────────────────────────────────

    def update_position(self, seconds: float):
        """Chiamato dal player video ad ogni tick"""
        self.state.video_position = seconds
        self._notify()

    def start_polling(self, interval_ms: int = 200):
        """
        Avvia un thread che legge la posizione dal player VLC
        (alternativa a callback diretto)
        """
        if self._position_thread and self._position_thread.is_alive():
            return

        self._stop_event.clear()

        def _poll():
            # Legge la posizione del player VLC in un loop.
            while not self._stop_event.is_set():
                if self.player_get_time and self.state.is_playing:
                    t = self.player_get_time()
                    if t >= 0:
                        self.update_position(t / 1000.0)  # VLC usa ms
            self._stop_event.wait(interval_ms / 1000.0)

        self._position_thread = Thread(target=_poll, daemon=True, name="SyncPoll")
        self._position_thread.start()

    def stop_polling(self):
        """Arresta il thread di polling della posizione video."""
        self._stop_event.set()

    # ──────────────────────────────────
    #  Snapshot timestamp per eventi
    # ──────────────────────────────────

    def snapshot(self) -> float:
        """
        Ritorna il timestamp video da associare all'evento appena inserito.
        Usa la posizione corrente del video.
        """
        return self.state.video_position

    def snapshot_with_delay(self, delay_seconds: float = -1.5) -> float:
        """
        Ritorna timestamp con offset negativo:
        l'evento è avvenuto 'delay' secondi prima del click dello scout
        """
        return max(0.0, self.state.video_position + delay_seconds)

    # ──────────────────────────────────
    #  Score / Rally tracking
    # ──────────────────────────────────

    def point_home(self):
        """Registra un punto per la squadra di casa."""
        self.state.score_home += 1
        self.state.rally_number += 1
        self._check_set_end()
        self._notify()

    def point_away(self):
        """Registra un punto per la squadra ospite."""
        self.state.score_away += 1
        self.state.rally_number += 1
        self._check_set_end()
        self._notify()

    def _check_set_end(self):
        # Verifica se il set è terminato e passa al successivo.
        h, a = self.state.score_home, self.state.score_away
        min_pts = 15 if self.state.set_number == 5 else 25
        if (h >= min_pts or a >= min_pts) and abs(h - a) >= 2:
            logger.info("🏐 Fine set %d: %d-%d", self.state.set_number, h, a)
            self.state.set_number += 1
            self.state.score_home = 0
            self.state.score_away = 0

    def new_set(self, set_number: int):
        """Imposta un nuovo numero di set azzerando il punteggio."""
        self.state.set_number = set_number
        self.state.score_home = 0
        self.state.score_away = 0
        self.state.rally_number = 1
        self._notify()

    # ──────────────────────────────────
    #  Seek video verso un evento
    # ──────────────────────────────────

    def get_seek_position(self, event_timestamp: float, pre_roll: float = 3.0) -> float:
        """
        Calcola la posizione di seek nel video per rivedere un evento.
        pre_roll = secondi prima dell'evento da mostrare
        """
        return max(0.0, event_timestamp - pre_roll)

    # ──────────────────────────────────
    #  Callbacks / Notifiche
    # ──────────────────────────────────

    def add_callback(self, fn: Callable[[SyncState], None]):
        """Registra funzione da chiamare ad ogni cambio di stato"""
        self._callbacks.append(fn)

    def remove_callback(self, fn: Callable[[SyncState], None]):
        """Rimuove una callback registrata."""
        self._callbacks.remove(fn)

    def _notify(self):
        # Notifica tutti i callback registrati del cambio stato.
        for cb in self._callbacks:
            try:
                cb(self.state)
            except Exception as e:
                logger.error("Callback error: %s", e)

    # ──────────────────────────────────
    #  Play/Pause stato
    # ──────────────────────────────────

    def set_playing(self, playing: bool):
        """Imposta lo stato di riproduzione del video."""
        self.state.is_playing = playing
        self._notify()
