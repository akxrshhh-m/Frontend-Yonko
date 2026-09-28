"""
Gran Tesoro VIP Gala & World Government Reverie Summit RSVP System
Main entry point - supports both CLI and API modes.
"""
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "cli"
    
    if mode == "api":
        # Run Flask API server
        from api.routes import create_app
        app = create_app()
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
        print(f"\n🏆 Gran Tesoro RSVP API starting on port {port}...")
        print(f"   API docs: http://localhost:{port}/api/health\n")
        app.run(debug=True, port=port)
    
    elif mode == "cli":
        # Run interactive CLI
        from cli.interface import CLIInterface
        cli = CLIInterface()
        cli.run()
    
    elif mode == "demo":
        # Run demo directly
        from cli.interface import CLIInterface
        cli = CLIInterface()
        from utils.theme import BANNER
        print(BANNER)
        cli._run_demo()
    
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python main.py [cli|api|demo] [port]")
        sys.exit(1)


if __name__ == "__main__":
    main()