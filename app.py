"""Punto di ingresso unificato per avviare le interfacce del gestionale."""

from __future__ import annotations

from typing import Callable, Dict, Tuple


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


OPTIONS: Dict[str, Tuple[str, Callable[[], None]]] = {
    "1": ("Interfaccia a menu testuale", launch_cli),
    "2": ("Interfaccia navigabile tipo foglio di calcolo", launch_tui),
    "3": ("Interfaccia grafica (Tkinter)", launch_gui),
}


def main() -> None:
    """Mostra un piccolo menu iniziale e avvia l'interfaccia scelta."""

    while True:
        print("\n================================")
        print(" Gestionale di magazzino - Avvio")
        print("================================")
        for key, (label, _) in OPTIONS.items():
            print(f" {key}. {label}")
        print(" 0. Esci")

        choice = input("\nSeleziona un'opzione: ").strip()
        if choice == "0":
            print("Chiusura del programma. A presto!")
            return
        action = OPTIONS.get(choice)
        if action is None:
            print("Opzione non valida. Riprova.")
            continue
        label, handler = action
        print(f"\nAvvio: {label}\n")
        handler()
        break


if __name__ == "__main__":
    main()
