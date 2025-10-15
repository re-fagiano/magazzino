"""Punto di ingresso unificato per avviare le interfacce del gestionale."""

from __future__ import annotations

import argparse
from typing import Callable, Dict, Optional, Sequence, Tuple


def launch_cli() -> None:
    """Avvia l'interfaccia testuale classica a menu."""

    from inventory_manager import main as cli_main

    cli_main()


def launch_tui() -> None:
    """Avvia l'interfaccia navigabile stile foglio di calcolo."""

    from inventory_tui import run as tui_run

    tui_run()


def launch_gui() -> None:
    """Avvia l'interfaccia grafica moderna basata su Tkinter."""

    from inventory_gui import run as gui_run

    gui_run()


INTERFACES: Dict[str, Tuple[str, Callable[[], None]]] = {
    "cli": ("Interfaccia a menu testuale", launch_cli),
    "tui": ("Interfaccia navigabile tipo foglio di calcolo", launch_tui),
    "gui": ("Interfaccia grafica (Tkinter)", launch_gui),
}


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Avvia l'interfaccia richiesta (GUI predefinita)."""

    parser = argparse.ArgumentParser(description="Gestionale di magazzino")
    parser.add_argument(
        "--interface",
        "-i",
        choices=tuple(INTERFACES.keys()),
        default="gui",
        help=(
            "Interfaccia da avviare: "
            "'gui' (predefinita), 'cli' per il menu testuale o 'tui' per la tabella curses."
        ),
    )
    args = parser.parse_args(argv)

    label, handler = INTERFACES[args.interface]
    if args.interface != "gui":
        print(f"Avvio: {label}\n")
    handler()


if __name__ == "__main__":
    main()
