"""
In-Memory Data Store - Gran Tesoro's Golden Vault
Thread-safe storage for all system entities.
"""
import threading
from typing import Dict, List, Optional
from collections import OrderedDict

from models.event import Event
from models.participant import Participant
from models.registration import Registration
from models.waitlist_entry import WaitlistEntry
from models.offer import SeatOffer


class Database:
    """
    Thread-safe in-memory database.
    Acts as Gran Tesoro's Golden Vault - storing all records securely.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for consistent data access."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._data_lock = threading.RLock()
        
        # Primary stores
        self.events: Dict[str, Event] = OrderedDict()
        self.participants: Dict[str, Participant] = OrderedDict()
        self.registrations: Dict[str, Registration] = OrderedDict()
        self.waitlist_entries: Dict[str, WaitlistEntry] = OrderedDict()
        self.offers: Dict[str, SeatOffer] = OrderedDict()
        
        # Index stores for fast lookups
        self._event_registrations: Dict[str, List[str]] = {}  # event_id -> [reg_ids]
        self._event_waitlist: Dict[str, List[str]] = {}  # event_id -> [waitlist_ids]
        self._participant_email_index: Dict[str, str] = {}  # email -> participant_id
        self._event_participant_reg: Dict[str, str] = {}  # "event_id:participant_id" -> reg_id
        self._event_participant_waitlist: Dict[str, str] = {}  # "event_id:participant_id" -> wl_id
        
        # Audit log
        self.audit_log: List[dict] = []
    
    def reset(self):
        """Reset all data (useful for testing)."""
        with self._data_lock:
            self.events.clear()
            self.participants.clear()
            self.registrations.clear()
            self.waitlist_entries.clear()
            self.offers.clear()
            self._event_registrations.clear()
            self._event_waitlist.clear()
            self._participant_email_index.clear()
            self._event_participant_reg.clear()
            self._event_participant_waitlist.clear()
            self.audit_log.clear()
    
    # ---- Event Operations ----
    def save_event(self, event: Event) -> Event:
        with self._data_lock:
            self.events[event.id] = event
            if event.id not in self._event_registrations:
                self._event_registrations[event.id] = []
            if event.id not in self._event_waitlist:
                self._event_waitlist[event.id] = []
            return event
    
    def get_event(self, event_id: str) -> Optional[Event]:
        with self._data_lock:
            return self.events.get(event_id)
    
    def get_all_events(self) -> List[Event]:
        with self._data_lock:
            return list(self.events.values())
    
    def delete_event(self, event_id: str) -> bool:
        with self._data_lock:
            if event_id in self.events:
                del self.events[event_id]
                self._event_registrations.pop(event_id, None)
                self._event_waitlist.pop(event_id, None)
                return True
            return False
    
    # ---- Participant Operations ----
    def save_participant(self, participant: Participant) -> Participant:
        with self._data_lock:
            self.participants[participant.id] = participant
            self._participant_email_index[participant.email.lower()] = participant.id
            return participant
    
    def get_participant(self, participant_id: str) -> Optional[Participant]:
        with self._data_lock:
            return self.participants.get(participant_id)
    
    def get_participant_by_email(self, email: str) -> Optional[Participant]:
        with self._data_lock:
            pid = self._participant_email_index.get(email.lower())
            return self.participants.get(pid) if pid else None
    
    def get_all_participants(self) -> List[Participant]:
        with self._data_lock:
            return list(self.participants.values())
    
    # ---- Registration Operations ----
    def save_registration(self, registration: Registration) -> Registration:
        with self._data_lock:
            self.registrations[registration.id] = registration
            key = f"{registration.event_id}:{registration.participant_id}"
            self._event_participant_reg[key] = registration.id
            if registration.event_id not in self._event_registrations:
                self._event_registrations[registration.event_id] = []
            if registration.id not in self._event_registrations[registration.event_id]:
                self._event_registrations[registration.event_id].append(registration.id)
            return registration
    
    def get_registration(self, registration_id: str) -> Optional[Registration]:
        with self._data_lock:
            return self.registrations.get(registration_id)
    
    def get_event_registrations(self, event_id: str, status: str = None) -> List[Registration]:
        with self._data_lock:
            reg_ids = self._event_registrations.get(event_id, [])
            regs = [self.registrations[rid] for rid in reg_ids if rid in self.registrations]
            if status:
                regs = [r for r in regs if r.status == status]
            return regs
    
    def get_active_registration_count(self, event_id: str) -> int:
        with self._data_lock:
            from config import RegistrationStatus
            reg_ids = self._event_registrations.get(event_id, [])
            return sum(
                1 for rid in reg_ids
                if rid in self.registrations
                and self.registrations[rid].status == RegistrationStatus.CONFIRMED
            )
    
    def find_registration(self, event_id: str, participant_id: str) -> Optional[Registration]:
        with self._data_lock:
            key = f"{event_id}:{participant_id}"
            reg_id = self._event_participant_reg.get(key)
            return self.registrations.get(reg_id) if reg_id else None
    
    # ---- Waitlist Operations ----
    def save_waitlist_entry(self, entry: WaitlistEntry) -> WaitlistEntry:
        with self._data_lock:
            self.waitlist_entries[entry.id] = entry
            key = f"{entry.event_id}:{entry.participant_id}"
            self._event_participant_waitlist[key] = entry.id
            if entry.event_id not in self._event_waitlist:
                self._event_waitlist[entry.event_id] = []
            if entry.id not in self._event_waitlist[entry.event_id]:
                self._event_waitlist[entry.event_id].append(entry.id)
            return entry
    
    def get_waitlist_entry(self, entry_id: str) -> Optional[WaitlistEntry]:
        with self._data_lock:
            return self.waitlist_entries.get(entry_id)
    
    def get_event_waitlist(self, event_id: str, active_only: bool = True) -> List[WaitlistEntry]:
        with self._data_lock:
            wl_ids = self._event_waitlist.get(event_id, [])
            entries = [self.waitlist_entries[wid] for wid in wl_ids if wid in self.waitlist_entries]
            if active_only:
                entries = [e for e in entries if e.is_active]
            entries.sort(key=lambda e: e.position)
            return entries
    
    def get_next_waitlist_position(self, event_id: str) -> int:
        with self._data_lock:
            entries = self.get_event_waitlist(event_id, active_only=False)
            return max((e.position for e in entries), default=0) + 1
    
    def find_waitlist_entry(self, event_id: str, participant_id: str) -> Optional[WaitlistEntry]:
        with self._data_lock:
            key = f"{event_id}:{participant_id}"
            wl_id = self._event_participant_waitlist.get(key)
            if wl_id and wl_id in self.waitlist_entries:
                entry = self.waitlist_entries[wl_id]
                return entry if entry.is_active else None
            return None
    
    # ---- Offer Operations ----
    def save_offer(self, offer: SeatOffer) -> SeatOffer:
        with self._data_lock:
            self.offers[offer.id] = offer
            return offer
    
    def get_offer(self, offer_id: str) -> Optional[SeatOffer]:
        with self._data_lock:
            return self.offers.get(offer_id)
    
    def get_pending_offers_for_event(self, event_id: str) -> List[SeatOffer]:
        with self._data_lock:
            from config import OfferStatus
            return [
                o for o in self.offers.values()
                if o.event_id == event_id and o.status == OfferStatus.PENDING
            ]
    
    def get_participant_offers(self, participant_id: str) -> List[SeatOffer]:
        with self._data_lock:
            return [o for o in self.offers.values() if o.participant_id == participant_id]
    
    # ---- Audit Log ----
    def add_audit_entry(self, action: str, entity_type: str, entity_id: str, details: str = ""):
        from utils.id_generator import timestamp
        with self._data_lock:
            self.audit_log.append({
                "timestamp": timestamp(),
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "details": details,
            })
    
    def get_audit_log(self, entity_id: str = None, limit: int = 50) -> List[dict]:
        with self._data_lock:
            logs = self.audit_log
            if entity_id:
                logs = [l for l in logs if l["entity_id"] == entity_id]
            return logs[-limit:]


# Global database instance
db = Database()