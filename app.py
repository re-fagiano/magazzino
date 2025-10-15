"""Punto di ingresso unificato per avviare le interfacce del gestionale."""

from __future__ import annotations

import os
from typing import Callable, Dict, Tuple


def launch_cli() -> bool:
    """Avvia l'interfaccia testuale classica a menu."""

    from inventory_manager import main as cli_main

    cli_main()
    return True


def _explain_missing_curses() -> None:
    """Show an explicit hint for enabling curses on the current platform."""

    print("\nImpossibile avviare l'interfaccia a tabella: il modulo 'curses' non è disponibile.")
    if os.name == "nt":
        print(
            "Su Windows installa il pacchetto opzionale 'windows-curses' eseguendo:\n"
            "    pip install windows-curses\n"
            "e poi riapri l'applicazione."
        )
    else:
        print("Installa le librerie di sistema per 'curses' oppure utilizza un'interfaccia alternativa.")


def launch_tui() -> bool:
    """Avvia l'interfaccia navigabile stile foglio di calcolo."""

    try:
        import curses  # noqa: F401  # Verifica preventiva della disponibilità del modulo
    except ModuleNotFoundError:
        _explain_missing_curses()
        return False

    try:
        from inventory_tui import run as tui_run
    except ModuleNotFoundError as exc:
        if getattr(exc, "name", None) in {"curses", "_curses"}:
            _explain_missing_curses()
            return False
        raise

    tui_run()
    return True


def launch_gui() -> bool:
    """Avvia l'interfaccia grafica basata su Tkinter."""

    try:
        from inventory_gui import run as gui_run
    except ModuleNotFoundError as exc:
        print("Errore: modulo mancante per l'interfaccia grafica.")
        print(f"Dettagli: {exc}")
        return False

    gui_run()
    return True


OPTIONS: Dict[str, Tuple[str, Callable[[], bool]]] = {
    "1": ("Interfaccia a menu testuale", launch_cli),
    "2": ("Interfaccia navigabile tipo foglio di calcolo", launch_tui),
    "3": ("Interfaccia grafica completa", launch_gui),
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
        success = handler()
        if success:
            break


if __name__ == "__main__":
    main()
