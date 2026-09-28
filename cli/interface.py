"""
CLI Interface - Gran Tesoro RSVP System
Interactive command-line interface for managing events.
"""
import sys
from services.event_service import EventService
from services.registration_service import RegistrationService
from services.waitlist_service import WaitlistService
from services.offer_service import OfferService
from storage.database import db
from utils.theme import BANNER, EVENT_TEMPLATES, FLAVOR_TEXT
from utils.validators import ValidationError


class CLIInterface:
    """Interactive CLI for the Gran Tesoro RSVP System."""
    
    def __init__(self):
        self.event_service = EventService()
        self.registration_service = RegistrationService()
        self.waitlist_service = WaitlistService()
        self.offer_service = OfferService()
    
    def run(self):
        """Main CLI loop."""
        print(BANNER)
        print("Welcome to the Gran Tesoro VIP Gala & Reverie Summit RSVP System!")
        print("Type 'help' for available commands.\n")
        
        while True:
            try:
                command = input("\n🏆 Gran Tesoro > ").strip().lower()
                
                if command in ("quit", "exit", "q"):
                    print("\n🚢 Sailing away from Gran Tesoro... Goodbye!")
                    break
                elif command == "help":
                    self._show_help()
                elif command == "create-event":
                    self._create_event()
                elif command == "create-template":
                    self._create_from_template()
                elif command == "list-events":
                    self._list_events()
                elif command == "event-details":
                    self._event_details()
                elif command == "event-summary":
                    self._event_summary()
                elif command == "update-capacity":
                    self._update_capacity()
                elif command == "register":
                    self._register_participant()
                elif command == "cancel-registration":
                    self._cancel_registration()
                elif command == "view-waitlist":
                    self._view_waitlist()
                elif command == "accept-offer":
                    self._accept_offer()
                elif command == "decline-offer":
                    self._decline_offer()
                elif command == "check-offers":
                    self._check_expired_offers()
                elif command == "offer-status":
                    self._offer_status()
                elif command == "participant-info":
                    self._participant_info()
                elif command == "close-event":
                    self._close_event()
                elif command == "cancel-event":
                    self._cancel_event()
                elif command == "audit-log":
                    self._show_audit_log()
                elif command == "demo":
                    self._run_demo()
                elif command == "":
                    continue
                else:
                    print(f"❓ Unknown command: '{command}'. Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                print("\n\n🚢 Sailing away from Gran Tesoro... Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def _show_help(self):
        """Display available commands."""
        print("""
╔════════════════════════════════════════════════════════════╗
║                    AVAILABLE COMMANDS                      ║
╠════════════════════════════════════════════════════════════╣
║                                                            ║
║  EVENT MANAGEMENT:                                         ║
║    create-event      - Create a new event                  ║
║    create-template   - Create event from One Piece template║
║    list-events       - List all events                     ║
║    event-details     - View event details                  ║
║    event-summary     - Full event summary with guests      ║
║    update-capacity   - Update event capacity               ║
║    close-event       - Close event for registrations       ║
║    cancel-event      - Cancel an event entirely            ║
║                                                            ║
║  REGISTRATION:                                             ║
║    register          - Register a participant              ║
║    cancel-registration - Cancel a registration             ║
║    participant-info  - View participant's registrations     ║
║                                                            ║
║  WAITLIST & OFFERS:                                        ║
║    view-waitlist     - View event waitlist                 ║
║    accept-offer      - Accept a seat offer                 ║
║    decline-offer     - Decline a seat offer                ║
║    check-offers      - Check for expired offers            ║
║    offer-status      - Check status of an offer            ║
║                                                            ║
║  SYSTEM:                                                   ║
║    audit-log         - View audit log                      ║
║    demo              - Run interactive demo                ║
║    help              - Show this help message              ║
║    quit / exit       - Exit the system                     ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
        """)
    
    def _create_event(self):
        """Create a new event interactively."""
        print("\n🎰 CREATE NEW EVENT")
        print("-" * 40)
        
        try:
            name = input("Event Name: ").strip()
            description = input("Description: ").strip()
            venue = input("Venue: ").strip()
            capacity = input("Capacity: ").strip()
            event_date = input("Event Date (YYYY-MM-DD HH:MM): ").strip()
            category = input("Category [VIP Gala]: ").strip() or "VIP Gala"
            
            result = self.event_service.create_event(
                name=name,
                description=description,
                venue=venue,
                capacity=int(capacity),
                event_date=event_date,
                category=category,
            )
            
            if result["success"]:
                event = result["event"]
                print(f"\n✅ {result['message']}")
                print(f"   Event ID: {event['id']}")
                print(f"   Name: {event['name']}")
                print(f"   Capacity: {event['capacity']}")
                print(f"   Status: {event['status']}")
            else:
                print(f"\n❌ {result['message']}")
        
        except ValidationError as e:
            print(f"\n❌ Validation Error: {e.message}")
        except ValueError as e:
            print(f"\n❌ Invalid input: {e}")
    
    def _create_from_template(self):
        """Create event from One Piece themed template."""
        print("\n🎰 CREATE FROM TEMPLATE")
        print("-" * 40)
        
        templates = list(EVENT_TEMPLATES.items())
        for i, (key, tmpl) in enumerate(templates, 1):
            print(f"  {i}. {tmpl['name']}")
            print(f"     📍 {tmpl['venue']} | 👥 Default Capacity: {tmpl['default_capacity']}")
        
        try:
            choice = int(input("\nSelect template (number): ").strip()) - 1
            if 0 <= choice < len(templates):
                key, tmpl = templates[choice]
                capacity = input(f"Capacity [{tmpl['default_capacity']}]: ").strip()
                capacity = int(capacity) if capacity else tmpl['default_capacity']
                event_date = input("Event Date (YYYY-MM-DD HH:MM): ").strip()
                
                result = self.event_service.create_event(
                    name=tmpl['name'],
                    description=tmpl['description'],
                    venue=tmpl['venue'],
                    capacity=capacity,
                    event_date=event_date,
                    category="Themed Event",
                )
                
                if result["success"]:
                    print(f"\n✅ {result['message']}")
                    print(f"   Event ID: {result['event']['id']}")
                else:
                    print(f"\n❌ {result['message']}")
            else:
                print("Invalid selection.")
        except (ValueError, IndexError) as e:
            print(f"\n❌ Invalid input: {e}")
    
    def _list_events(self):
        """List all events."""
        events = self.event_service.list_events()
        
        if not events:
            print("\n📋 No events found.")
            return
        
        print(f"\n📋 EVENTS ({len(events)} total)")
        print("=" * 80)
        
        for event in events:
            stats = event.get("stats", {})
            status_icon = {"OPEN": "🟢", "FULL": "🔴", "CLOSED": "⚫", "CANCELLED": "❌"}.get(
                event["status"], "⚪"
            )
            print(f"\n  {status_icon} [{event['id']}] {event['name']}")
            print(f"     📍 {event['venue']} | 📅 {event['event_date']}")
            print(f"     👥 {stats.get('confirmed_registrations', 0)}/{event['capacity']} "
                  f"| ⏳ Waitlist: {stats.get('waitlist_count', 0)} "
                  f"| 🪑 Available: {stats.get('available_seats', 0)}")
        
        print("\n" + "=" * 80)
    
    def _event_details(self):
        """View event details."""
        event_id = input("Event ID: ").strip()
        result = self.event_service.get_event(event_id)
        
        if not result:
            print("\n❌ Event not found.")
            return
        
        stats = result.get("stats", {})
        print(f"\n🎪 EVENT DETAILS")
        print("=" * 50)
        print(f"  ID:          {result['id']}")
        print(f"  Name:        {result['name']}")
        print(f"  Description: {result['description']}")
        print(f"  Venue:       {result['venue']}")
        print(f"  Date:        {result['event_date']}")
        print(f"  Organizer:   {result['organizer']}")
        print(f"  Category:    {result['category']}")
        print(f"  Status:      {result['status']}")
        print(f"  Capacity:    {result['capacity']}")
        print(f"  Confirmed:   {stats.get('confirmed_registrations', 0)}")
        print(f"  Available:   {stats.get('available_seats', 0)}")
        print(f"  Waitlisted:  {stats.get('waitlist_count', 0)}")
        print("=" * 50)
    
    def _event_summary(self):
        """View comprehensive event summary."""
        event_id = input("Event ID: ").strip()
        result = self.event_service.get_event_summary(event_id)
        
        if not result:
            print("\n❌ Event not found.")
            return
        
        event = result["event"]
        stats = result["stats"]
        
        print(f"\n🏆 EVENT SUMMARY: {event['name']}")
        print("=" * 60)
        print(f"  Status: {event['status']} | Occupancy: {stats['occupancy_percentage']}%")
        print(f"  Seats: {stats['confirmed_count']}/{stats['capacity']} "
              f"| Available: {stats['available_seats']}")
        print(f"  Waitlist: {stats['waitlist_count']} | Pending Offers: {stats['pending_offers']}")
        
        if result["confirmed_guests"]:
            print(f"\n  🌟 CONFIRMED GUESTS ({stats['confirmed_count']}):")
            for guest in result["confirmed_guests"]:
                reg = guest["registration"]
                p = guest["participant"]
                print(f"    #{reg['registration_number']} {p['name']} ({p['email']}) "
                      f"- {reg['vip_tier']}")
        
        if result["waitlist_guests"]:
            print(f"\n  ⏳ WAITLIST ({stats['waitlist_count']}):")
            for guest in result["waitlist_guests"]:
                wl = guest["waitlist_entry"]
                p = guest["participant"]
                print(f"    #{wl['position']} {p['name']} ({p['email']}) - {wl['rank_title']}")
        
        print("=" * 60)
    
    def _update_capacity(self):
        """Update event capacity."""
        event_id = input("Event ID: ").strip()
        capacity = input("New Capacity: ").strip()
        
        try:
            result = self.event_service.update_capacity(event_id, int(capacity))
            if result["success"]:
                print(f"\n✅ {result['message']}")
                print(f"   Old: {result['old_capacity']} → New: {result['new_capacity']}")
                if result.get('promotions_available', 0) > 0:
                    print(f"   📢 {result['promotions_available']} seats can now be offered to waitlisted guests!")
            else:
                print(f"\n❌ {result['message']}")
        except (ValidationError, ValueError) as e:
            print(f"\n❌ Error: {e}")
    
    def _register_participant(self):
        """Register a participant for an event."""
        print("\n📝 REGISTER PARTICIPANT")
        print("-" * 40)
        
        event_id = input("Event ID: ").strip()
        name = input("Participant Name: ").strip()
        email = input("Email: ").strip()
        phone = input("Phone [optional]: ").strip()
        affiliation = input("Affiliation [Independent]: ").strip() or "Independent"
        
        try:
            result = self.registration_service.register_participant(
                event_id=event_id,
                name=name,
                email=email,
                phone=phone,
                affiliation=affiliation,
            )
            
            if result["success"]:
                if result.get("type") == "CONFIRMED":
                    reg = result["registration"]
                    print(f"\n✅ {result['message']}")
                    print(f"   Registration ID: {reg['id']}")
                    print(f"   VIP Tier: {result['vip_tier']}")
                    print(f"   Seat #: {reg['registration_number']}")
                elif result.get("type") == "WAITLISTED":
                    wl = result["waitlist_entry"]
                    print(f"\n⏳ {result['message']}")
                    print(f"   Waitlist Position: #{wl['position']}")
                    print(f"   Priority: {result['rank_title']}")
            else:
                print(f"\n❌ {result['message']}")
        
        except ValidationError as e:
            print(f"\n❌ Validation Error: {e.message}")
    
    def _cancel_registration(self):
        """Cancel a registration."""
        event_id = input("Event ID: ").strip()
        print("Cancel by: (1) Email  (2) Registration ID  (3) Participant ID")
        choice = input("Choice: ").strip()
        
        kwargs = {"event_id": event_id}
        if choice == "1":
            kwargs["email"] = input("Email: ").strip()
        elif choice == "2":
            kwargs["registration_id"] = input("Registration ID: ").strip()
        elif choice == "3":
            kwargs["participant_id"] = input("Participant ID: ").strip()
        else:
            print("Invalid choice.")
            return
        
        result = self.registration_service.cancel_registration(**kwargs)
        
        if result["success"]:
            print(f"\n✅ {result['message']}")
            print(f"   Cancelled: {result.get('participant_name', 'Unknown')}")
            
            if result.get("waitlist_offer", {}).get("success"):
                offer = result["waitlist_offer"]
                print(f"\n📞 {FLAVOR_TEXT['offer_sent']}")
                if offer.get("participant"):
                    print(f"   Next in line: {offer['participant']['name']}")
                print(f"   Offer ID: {offer['offer']['id']}")
            elif result.get("waitlist_status"):
                print(f"   Waitlist: {result['waitlist_status']}")
        else:
            print(f"\n❌ {result['message']}")
    
    def _view_waitlist(self):
        """View waitlist for an event."""
        event_id = input("Event ID: ").strip()
        result = self.waitlist_service.get_waitlist(event_id)
        
        if not result["success"]:
            print(f"\n❌ {result['message']}")
            return
        
        print(f"\n📋 SILVER ROOM QUEUE - {result['event']['name']}")
        print(f"   Total Waitlisted: {result['waitlist_count']}")
        print("=" * 60)
        
        if not result["waitlist"]:
            print("   (Empty - no one is waiting)")
        else:
            for entry in result["waitlist"]:
                wl = entry["waitlist_entry"]
                p = entry.get("participant", {})
                print(f"   #{wl['position']} | {p.get('name', 'Unknown')} "
                      f"({p.get('email', 'N/A')}) | {wl['rank_title']}")
        
        print("=" * 60)
    
    def _accept_offer(self):
        """Accept a seat offer."""
        offer_id = input("Offer ID: ").strip()
        result = self.offer_service.accept_offer(offer_id)
        
        if result["success"]:
            print(f"\n✅ {result['message']}")
            if result.get("registration"):
                print(f"   Registration ID: {result['registration']['id']}")
        else:
            print(f"\n❌ {result['message']}")
    
    def _decline_offer(self):
        """Decline a seat offer."""
        offer_id = input("Offer ID: ").strip()
        result = self.offer_service.decline_offer(offer_id)
        
        if result["success"]:
            print(f"\n✅ {result['message']}")
            if result.get("next_offer"):
                print(f"   Next offer created: {result['next_offer']['offer']['id']}")
        else:
            print(f"\n❌ {result['message']}")
    
    def _check_expired_offers(self):
        """Check for expired offers."""
        event_id = input("Event ID (or press Enter for all): ").strip() or None
        result = self.offer_service.check_and_expire_offers(event_id)
        
        print(f"\n🔍 Offer Check Results:")
        print(f"   Expired: {result['expired_count']}")
        print(f"   New Offers Created: {result['next_offers_created']}")
    
    def _offer_status(self):
        """Check offer status."""
        offer_id = input("Offer ID: ").strip()
        result = self.offer_service.get_offer_status(offer_id)
        
        if result["success"]:
            offer = result["offer"]
            print(f"\n🎫 OFFER STATUS")
            print(f"   ID: {offer['id']}")
            print(f"   Status: {offer['status']}")
            print(f"   Participant: {result.get('participant', {}).get('name', 'Unknown')}")
            print(f"   Event: {result.get('event', {}).get('name', 'Unknown')}")
            if offer['status'] == 'PENDING':
                print(f"   Time Remaining: {offer['time_remaining_seconds']}s")
                print(f"   Expires At: {offer['expires_at']}")
        else:
            print(f"\n❌ {result['message']}")
    
    def _participant_info(self):
        """View participant information."""
        email = input("Participant Email: ").strip()
        result = self.registration_service.get_participant_registrations(email=email)
        
        if not result["success"]:
            print(f"\n❌ {result['message']}")
            return
        
        p = result["participant"]
        print(f"\n👤 PARTICIPANT: {p['name']}")
        print(f"   Email: {p['email']} | Affiliation: {p['affiliation']}")
        
        if result["registrations"]:
            print(f"\n   📋 Registrations ({len(result['registrations'])}):")
            for item in result["registrations"]:
                reg = item["registration"]
                evt = item.get("event", {})
                print(f"      [{reg['status']}] {evt.get('name', 'N/A')} - {reg['vip_tier']}")
        
        if result["waitlist_entries"]:
            print(f"\n   ⏳ Waitlisted ({len(result['waitlist_entries'])}):")
            for item in result["waitlist_entries"]:
                wl = item["waitlist_entry"]
                evt = item.get("event", {})
                print(f"      #{wl['position']} {evt.get('name', 'N/A')} - {wl['rank_title']}")
        
        if result["pending_offers"]:
            print(f"\n   📞 Pending Offers ({len(result['pending_offers'])}):")
            for item in result["pending_offers"]:
                off = item["offer"]
                evt = item.get("event", {})
                print(f"      [{off['status']}] {evt.get('name', 'N/A')} - Offer: {off['id']}")
    
    def _close_event(self):
        """Close an event."""
        event_id = input("Event ID: ").strip()
        result = self.event_service.close_event(event_id)
        print(f"\n{'✅' if result['success'] else '❌'} {result['message']}")
    
    def _cancel_event(self):
        """Cancel an event."""
        event_id = input("Event ID: ").strip()
        confirm = input("Are you sure? This will cancel all registrations. (yes/no): ").strip()
        if confirm.lower() != "yes":
            print("Cancelled.")
            return
        result = self.event_service.cancel_event(event_id)
        if result["success"]:
            print(f"\n✅ {result['message']}")
            print(f"   Cancelled Registrations: {result['cancelled_registrations']}")
            print(f"   Cancelled Waitlist: {result['cancelled_waitlist']}")
        else:
            print(f"\n❌ {result['message']}")
    
    def _show_audit_log(self):
        """Show audit log."""
        entity_id = input("Filter by Entity ID (or press Enter for all): ").strip() or None
        logs = db.get_audit_log(entity_id=entity_id, limit=20)
        
        print(f"\n📜 AUDIT LOG (Last {len(logs)} entries)")
        print("=" * 70)
        for log in logs:
            print(f"  [{log['timestamp'][:19]}] {log['action']} | "
                  f"{log['entity_type']}:{log['entity_id']}")
            if log['details']:
                print(f"    → {log['details']}")
        print("=" * 70)
    
    def _run_demo(self):
        """Run an interactive demo showcasing all features."""
        print("\n" + "=" * 60)
        print("🎬 RUNNING GRAN TESORO RSVP DEMO")
        print("=" * 60)
        
        # Step 1: Create Event
        print("\n📌 Step 1: Creating 'Gran Tesoro VIP Golden Gala' (Capacity: 3)")
        result = self.event_service.create_event(
            name="Gran Tesoro VIP Golden Gala",
            description="An exclusive evening at Gild Tesoro's legendary golden casino ship!",
            venue="Gran Tesoro - Entertainment City",
            capacity=3,
            event_date="2025-12-31 20:00",
            category="VIP Gala",
        )
        event_id = result["event"]["id"]
        print(f"   ✅ Event created: {event_id}")
        
        # Step 2: Register participants
        guests = [
            ("Monkey D. Luffy", "luffy@strawhat.com", "Straw Hat Pirates"),
            ("Roronoa Zoro", "zoro@strawhat.com", "Straw Hat Pirates"),
            ("Nami", "nami@strawhat.com", "Straw Hat Pirates"),
            ("Sanji", "sanji@strawhat.com", "Straw Hat Pirates"),  # Should be waitlisted
            ("Nico Robin", "robin@strawhat.com", "Straw Hat Pirates"),  # Should be waitlisted
        ]
        
        registrations = []
        for name, email, affiliation in guests:
            print(f"\n📌 Registering: {name}")
            result = self.registration_service.register_participant(
                event_id=event_id,
                name=name,
                email=email,
                affiliation=affiliation,
            )
            if result["success"]:
                reg_type = result.get("type", "UNKNOWN")
                if reg_type == "CONFIRMED":
                    print(f"   ✅ CONFIRMED - Seat #{result['registration']['registration_number']} "
                          f"({result['vip_tier']})")
                    registrations.append(result)
                elif reg_type == "WAITLISTED":
                    print(f"   ⏳ WAITLISTED - Position #{result['waitlist_entry']['position']} "
                          f"({result['rank_title']})")
            else:
                print(f"   ❌ {result['message']}")
        
        # Step 3: Show event summary
        print("\n📌 Step 3: Event Summary")
        summary = self.event_service.get_event_summary(event_id)
        stats = summary["stats"]
        print(f"   Confirmed: {stats['confirmed_count']}/{stats['capacity']}")
        print(f"   Waitlisted: {stats['waitlist_count']}")
        print(f"   Occupancy: {stats['occupancy_percentage']}%")
        
        # Step 4: Cancel a registration
        print("\n📌 Step 4: Zoro cancels his registration (he got lost)")
        result = self.registration_service.cancel_registration(
            event_id=event_id,
            email="zoro@strawhat.com",
        )
        if result["success"]:
            print(f"   ✅ {result['message']}")
            if result.get("waitlist_offer", {}).get("success"):
                offer = result["waitlist_offer"]
                offer_id = offer["offer"]["id"]
                print(f"   📞 Offer sent to: {offer['participant']['name']}")
                print(f"   🎫 Offer ID: {offer_id}")
                
                # Step 5: Accept the offer
                print(f"\n📌 Step 5: {offer['participant']['name']} accepts the offer!")
                accept_result = self.offer_service.accept_offer(offer_id)
                if accept_result["success"]:
                    print(f"   ✅ {accept_result['message']}")
                else:
                    print(f"   ❌ {accept_result['message']}")
        
        # Step 6: Final summary
        print("\n📌 Step 6: Final Event Summary")
        summary = self.event_service.get_event_summary(event_id)
        stats = summary["stats"]
        print(f"   Confirmed: {stats['confirmed_count']}/{stats['capacity']}")
        print(f"   Waitlisted: {stats['waitlist_count']}")
        print(f"   Cancelled: {stats['cancelled_count']}")
        
        print("\n   🌟 Confirmed Guests:")
        for guest in summary["confirmed_guests"]:
            p = guest["participant"]
            r = guest["registration"]
            print(f"      {p['name']} - {r['vip_tier']}")
        
        if summary["waitlist_guests"]:
            print("\n   ⏳ Still Waitlisted:")
            for guest in summary["waitlist_guests"]:
                p = guest["participant"]
                wl = guest["waitlist_entry"]
                print(f"      #{wl['position']} {p['name']} - {wl['rank_title']}")
        
        print("\n" + "=" * 60)
        print("🎬 DEMO COMPLETE!")
        print("=" * 60)