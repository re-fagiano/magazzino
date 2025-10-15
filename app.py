"""Punto di ingresso unificato per avviare le interfacce del gestionale."""

from __future__ import annotations

import os
from typing import Callable, Dict, Tuple


def launch_cli() -> None:
    """Avvia l'interfaccia testuale classica a menu."""

    from inventory_manager import main as cli_main

    cli_main()


def launch_tui() -> None:
    """Avvia l'interfaccia navigabile stile foglio di calcolo."""

    try:
        from inventory_tui import run as tui_run
    except ModuleNotFoundError as exc:
        if exc.name in {"curses", "_curses"}:
            print("\nImpossibile avviare l'interfaccia a tabella: il modulo 'curses' non è disponibile.")
            if os.name == "nt":
                print(
                    "Su Windows installa il pacchetto opzionale 'windows-curses' eseguendo:\n"
                    "    pip install windows-curses\n"
                    "e poi riapri l'applicazione."
                )
            else:
                print(
                    "Installa le librerie di sistema per 'curses' oppure utilizza la versione a menu."
                )
            return
        raise

    tui_run()


OPTIONS: Dict[str, Tuple[str, Callable[[], None]]] = {
    "1": ("Interfaccia a menu testuale", launch_cli),
    "2": ("Interfaccia navigabile tipo foglio di calcolo", launch_tui),
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
