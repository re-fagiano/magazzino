"""Curses-based interface for the warehouse inventory manager.

This module offers a navigable table view inspired by spreadsheet
applications.  Users can scroll through the inventory, apply filters,
add, edit, and delete products directly from a terminal-friendly
interface while reusing the persistence layer implemented in
``inventory_manager.py``.
"""

from __future__ import annotations

import curses

BUTTON1_CLICKED = getattr(curses, "BUTTON1_CLICKED", 0)
BUTTON1_DOUBLE_CLICKED = getattr(curses, "BUTTON1_DOUBLE_CLICKED", 0)
BUTTON4_PRESSED = getattr(curses, "BUTTON4_PRESSED", 0)
BUTTON5_PRESSED = getattr(curses, "BUTTON5_PRESSED", 0)
from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

import inventory_manager as manager


TableRow = manager.ProductRow


@dataclass
class Column:
    """Representation of a column in the table."""

    title: str
    width: int
    accessor: Callable[[TableRow], str]


COLUMNS: Sequence[Column] = (
    Column("ID", 4, lambda row: str(row[0])),
    Column("Codice", 12, lambda row: row[1]),
    Column("Nome", 18, lambda row: row[2]),
    Column("Descrizione", 24, lambda row: row[3]),
    Column("Categoria", 12, lambda row: row[4]),
    Column("Quantità", 9, lambda row: str(row[5])),
    Column("Prezzo", 10, lambda row: f"{row[6]:.2f}"),
    Column("Posizione", 12, lambda row: row[7]),
    Column("Valore", 12, lambda row: f"{row[5] * row[6]:.2f}"),
)


class InventoryTUI:
    """Main controller for the curses-based inventory interface."""

    def __init__(self, stdscr: "curses._CursesWindow") -> None:
        self.stdscr = stdscr
        self.rows: List[TableRow] = []
        self.selected_index = 0
        self.top_row = 0
        self.status_message = "Premi 'h' per la guida rapida."
        self.order_by: Optional[str] = None
        self.descending = False
        self.filter_description = "Tutti i prodotti"
        self.data_loader: Callable[[], List[TableRow]] = lambda: manager.get_all_products(
            self.order_by, self.descending
        )

    # ------------------------------------------------------------------
    # Data handling
    # ------------------------------------------------------------------
    def refresh_data(self) -> None:
        try:
            self.rows = self.data_loader()
        except Exception as exc:  # pragma: no cover - defensive
            self.rows = []
            self.set_status(f"Errore nel caricamento dei dati: {exc}", error=True)
        else:
            self._clamp_selection()

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def set_status(self, message: str, *, error: bool = False) -> None:
        prefix = "[ERRORE] " if error else ""
        self.status_message = prefix + message

    def _clamp_selection(self) -> None:
        if not self.rows:
            self.selected_index = 0
            self.top_row = 0
            return
        self.selected_index = max(0, min(self.selected_index, len(self.rows) - 1))
        if self.selected_index < self.top_row:
            self.top_row = self.selected_index
        visible_height = self.table_height
        if self.selected_index >= self.top_row + visible_height:
            self.top_row = self.selected_index - visible_height + 1

    # ------------------------------------------------------------------
    # Layout properties
    # ------------------------------------------------------------------
    @property
    def height(self) -> int:
        return self.stdscr.getmaxyx()[0]

    @property
    def width(self) -> int:
        return self.stdscr.getmaxyx()[1]

    @property
    def table_height(self) -> int:
        # Reserve 4 rows: title, header, separator, status/help line
        return max(0, self.height - 4)

    # ------------------------------------------------------------------
    # Drawing methods
    # ------------------------------------------------------------------
    def draw(self) -> None:
        self.stdscr.erase()
        self._draw_title()
        self._draw_table()
        self._draw_status_bar()
        self.stdscr.refresh()

    def _draw_title(self) -> None:
        title = " Gestione Magazzino - Interfaccia a Tabelle "
        info = f" | Ordinamento: {self.order_by or 'predefinito'}"
        if self.order_by:
            info += " ↓" if self.descending else " ↑"
        info += f" | Filtro: {self.filter_description}"
        full_title = title + info
        trimmed = full_title[: self.width - 1]
        self.stdscr.addstr(0, 0, trimmed, curses.A_REVERSE)

    def _draw_table(self) -> None:
        y = 1
        header = self._format_row([col.title for col in COLUMNS])
        self.stdscr.addstr(y, 0, header)
        y += 1
        separator = self._format_row(["-" * col.width for col in COLUMNS])
        self.stdscr.addstr(y, 0, separator)
        y += 1

        if not self.rows:
            message = "Nessun dato da mostrare.".ljust(self.width - 1)
            self.stdscr.addstr(y, 0, message)
            return

        max_rows = self.table_height
        visible_rows = self.rows[self.top_row : self.top_row + max_rows]

        for idx, row in enumerate(visible_rows):
            global_index = self.top_row + idx
            line = self._format_row([col.accessor(row) for col in COLUMNS])
            attr = curses.A_NORMAL
            if global_index == self.selected_index:
                attr |= curses.A_REVERSE
            self.stdscr.addstr(y + idx, 0, line, attr)

    def _draw_status_bar(self) -> None:
        help_line = (
            "Mouse: click seleziona/doppio click dettagli | Frecce: naviga | Invio: dettagli | "
            "a: aggiungi | e: modifica | d: elimina | f: filtri | /: cerca | o: ordina | O: verso | "
            "r: aggiorna | t: valore | x: CSV | q: esci"
        )
        y = self.height - 2
        if y >= 0:
            self.stdscr.addstr(y, 0, help_line[: self.width - 1], curses.A_DIM)
        status = self.status_message[: self.width - 1]
        self.stdscr.addstr(self.height - 1, 0, status, curses.A_REVERSE)

    def _format_row(self, cells: Sequence[str]) -> str:
        parts = []
        for column, cell in zip(COLUMNS, cells):
            text = cell.replace("\n", " ")[: column.width]
            parts.append(text.ljust(column.width))
        row_text = " ".join(parts)
        return row_text[: self.width - 1]

    # ------------------------------------------------------------------
    # Event loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        manager.initialize_database()
        self.refresh_data()
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
            curses.mouseinterval(150)
        except curses.error:  # pragma: no cover - defensive on limited terminals
            pass
        while True:
            self.draw()
            key = self.stdscr.getch()
            if key == curses.KEY_RESIZE:
                self._clamp_selection()
                continue
            if key == curses.KEY_MOUSE:
                self._handle_mouse()
                continue
            if key in (ord("q"), ord("Q")):
                break
            self._handle_key(key)

    def _handle_key(self, key: int) -> None:
        if key in (curses.KEY_DOWN, ord("j")):
            self._move_selection(1)
        elif key in (curses.KEY_UP, ord("k")):
            self._move_selection(-1)
        elif key in (curses.KEY_NPAGE,):
            self._move_selection(self.table_height)
        elif key in (curses.KEY_PPAGE,):
            self._move_selection(-self.table_height)
        elif key in (curses.KEY_HOME,):
            self.selected_index = 0
            self.top_row = 0
        elif key in (curses.KEY_END,):
            self.selected_index = max(0, len(self.rows) - 1)
            self._clamp_selection()
        elif key in (ord("r"), ord("R")):
            self.refresh_data()
            self.set_status("Dati aggiornati.")
        elif key in (ord("/"),):
            self._search_dialog()
        elif key in (ord("f"), ord("F")):
            self._filter_dialog()
        elif key in (ord("o"),):
            self._ordering_dialog()
        elif key in (ord("O"),):
            self.descending = not self.descending
            self.refresh_data()
            self.set_status("Ordinamento aggiornato.")
        elif key in (ord("a"), ord("A")):
            self._add_product_dialog()
        elif key in (ord("e"), ord("E")):
            self._edit_product_dialog()
        elif key in (ord("d"), ord("D")):
            self._delete_selected()
        elif key in (ord("t"), ord("T")):
            total = manager.calculate_total_value()
            self.set_status(f"Valore totale inventario: € {total:.2f}")
        elif key in (ord("x"), ord("X")):
            filename = self._prompt_input("Nome file CSV (vuoto = default): ")
            try:
                path = manager.export_to_csv(filename or None)
            except Exception as exc:  # pragma: no cover - defensive
                self.set_status(f"Errore esportazione: {exc}", error=True)
            else:
                self.set_status(f"Esportato in {path}")
        elif key in (curses.KEY_ENTER, 10, 13):
            self._show_details()
        elif key in (ord("h"), ord("H")):
            self.set_status(
                "Naviga con le frecce, usa i comandi in basso per gestire l'inventario."
            )

    def _handle_mouse(self) -> None:
        try:
            _id, x, y, _z, state = curses.getmouse()
        except curses.error:  # pragma: no cover - defensive
            return

        if state & BUTTON1_CLICKED:
            self._select_row_at(y)
        elif state & BUTTON1_DOUBLE_CLICKED:
            if self._select_row_at(y):
                self._show_details()
        elif state & BUTTON4_PRESSED:
            self._move_selection(-1)
        elif state & BUTTON5_PRESSED:
            self._move_selection(1)

    def _select_row_at(self, y: int) -> bool:
        table_start = 3  # header (1) + separator (1) + first data row offset
        if y < table_start:
            return False
        relative = y - table_start
        if relative < 0 or relative >= self.table_height:
            return False
        index = self.top_row + relative
        if not self.rows or index >= len(self.rows):
            return False
        self.selected_index = index
        self._clamp_selection()
        return True

    def _move_selection(self, delta: int) -> None:
        if not self.rows:
            return
        self.selected_index = max(0, min(self.selected_index + delta, len(self.rows) - 1))
        if self.selected_index < self.top_row:
            self.top_row = self.selected_index
        visible_height = self.table_height
        if self.selected_index >= self.top_row + visible_height:
            self.top_row = self.selected_index - visible_height + 1

    # ------------------------------------------------------------------
    # Dialog helpers
    # ------------------------------------------------------------------
    def _prompt_input(self, prompt: str) -> str:
        curses.echo()
        try:
            self.stdscr.addstr(self.height - 1, 0, " " * (self.width - 1), curses.A_REVERSE)
            self.stdscr.addstr(self.height - 1, 0, prompt, curses.A_REVERSE)
            self.stdscr.refresh()
            value = self.stdscr.getstr(self.height - 1, len(prompt), self.width - len(prompt) - 1)
            return value.decode("utf-8").strip()
        finally:
            curses.noecho()

    def _prompt_int(self, prompt: str, *, allow_empty: bool = False) -> Optional[int]:
        while True:
            value = self._prompt_input(prompt)
            if allow_empty and not value:
                return None
            try:
                return int(value)
            except ValueError:
                self.set_status("Inserisci un numero intero valido.", error=True)

    def _prompt_float(self, prompt: str, *, allow_empty: bool = False) -> Optional[float]:
        while True:
            value = self._prompt_input(prompt)
            if allow_empty and not value:
                return None
            try:
                return float(value.replace(",", "."))
            except ValueError:
                self.set_status("Inserisci un numero valido.", error=True)

    def _prompt_yes_no(self, prompt: str) -> bool:
        answer = self._prompt_input(prompt + " (s/N): ").lower()
        return answer == "s"

    # ------------------------------------------------------------------
    # Feature dialogs
    # ------------------------------------------------------------------
    def _search_dialog(self) -> None:
        term = self._prompt_input("Cerca per codice/nome: ")
        if not term:
            return
        self.data_loader = lambda: manager.search_products(term, self.order_by, self.descending)
        self.filter_description = f"Ricerca '{term}'"
        self.refresh_data()
        self.set_status("Ricerca applicata.")

    def _filter_dialog(self) -> None:
        options = {
            "1": "Categoria",
            "2": "Posizione",
            "3": "Soglia quantità",
            "0": "Nessun filtro",
        }
        choice = self._prompt_input(
            "Filtro (1=categoria, 2=posizione, 3=soglia, 0=nessuno): "
        )
        if choice == "1":
            category = self._prompt_input("Categoria da filtrare: ")
            if category:
                self.data_loader = lambda: manager.filter_by_category(
                    category, self.order_by, self.descending
                )
                self.filter_description = f"Categoria '{category}'"
        elif choice == "2":
            location = self._prompt_input("Posizione da filtrare: ")
            if location:
                self.data_loader = lambda: manager.filter_by_location(
                    location, self.order_by, self.descending
                )
                self.filter_description = f"Posizione '{location}'"
        elif choice == "3":
            threshold = self._prompt_int("Quantità massima: ")
            if threshold is not None:
                self.data_loader = lambda: manager.get_low_stock_items(threshold)
                self.filter_description = f"<= {threshold}"
        elif choice == "0":
            self.data_loader = lambda: manager.get_all_products(self.order_by, self.descending)
            self.filter_description = "Tutti i prodotti"
        else:
            self.set_status("Scelta filtro non valida.", error=True)
            return
        self.refresh_data()
        self.set_status("Filtro aggiornato.")

    def _ordering_dialog(self) -> None:
        field = self._prompt_input(
            "Campo ordinamento (id, code, name, quantity, price, category, location): "
        )
        if not field:
            self.order_by = None
        elif field not in manager.ORDERABLE_COLUMNS:
            self.set_status("Campo non valido.", error=True)
            return
        else:
            self.order_by = field
        self.refresh_data()
        self.set_status("Ordinamento aggiornato.")

    def _add_product_dialog(self) -> None:
        code = self._prompt_input("Codice: ")
        name = self._prompt_input("Nome: ")
        description = self._prompt_input("Descrizione: ")
        category = self._prompt_input("Categoria: ")
        quantity = self._prompt_int("Quantità: ")
        price = self._prompt_float("Prezzo unitario: ")
        location = self._prompt_input("Posizione: ")
        if None in (quantity, price) or not code or not name:
            self.set_status("Inserimento annullato: dati insufficienti.", error=True)
            return
        try:
            manager.add_product(code, name, description, category, quantity, price, location)
        except Exception as exc:  # pragma: no cover - defensive
            self.set_status(f"Errore nell'aggiunta: {exc}", error=True)
        else:
            self.refresh_data()
            self.set_status("Prodotto aggiunto correttamente.")

    def _edit_product_dialog(self) -> None:
        row = self._current_row()
        if row is None:
            self.set_status("Nessun prodotto selezionato.", error=True)
            return
        self.set_status("Lascia vuoto per mantenere il valore attuale.")
        name = self._prompt_input(f"Nuovo nome ({row[2]}): ") or None
        description = self._prompt_input(f"Nuova descrizione ({row[3]}): ") or None
        category = self._prompt_input(f"Nuova categoria ({row[4]}): ") or None
        quantity = self._prompt_int("Nuova quantità (vuoto = invariata): ", allow_empty=True)
        price = self._prompt_float("Nuovo prezzo (vuoto = invariato): ", allow_empty=True)
        location = self._prompt_input(f"Nuova posizione ({row[7]}): ") or None
        try:
            updated = manager.update_product(
                row[0],
                name=name,
                description=description,
                category=category,
                quantity=quantity,
                price=price,
                location=location,
            )
        except Exception as exc:  # pragma: no cover - defensive
            self.set_status(f"Errore aggiornamento: {exc}", error=True)
            return
        if updated:
            self.refresh_data()
            self.set_status("Prodotto aggiornato.")
        else:  # pragma: no cover - dovrebbe esistere sempre
            self.set_status("Prodotto non trovato.", error=True)

    def _delete_selected(self) -> None:
        row = self._current_row()
        if row is None:
            self.set_status("Nessun prodotto selezionato.", error=True)
            return
        if not self._prompt_yes_no(f"Eliminare '{row[2]}' (ID {row[0]})?"):
            self.set_status("Eliminazione annullata.")
            return
        try:
            deleted = manager.delete_product(row[0])
        except Exception as exc:  # pragma: no cover - defensive
            self.set_status(f"Errore eliminazione: {exc}", error=True)
            return
        if deleted:
            self.refresh_data()
            self.set_status("Prodotto eliminato.")
        else:  # pragma: no cover - dovrebbe esistere sempre
            self.set_status("Prodotto non trovato.", error=True)

    def _show_details(self) -> None:
        row = self._current_row()
        if row is None:
            self.set_status("Nessun prodotto selezionato.", error=True)
            return
        details = [
            f"ID: {row[0]}",
            f"Codice: {row[1]}",
            f"Nome: {row[2]}",
            f"Descrizione: {row[3] or '-'}",
            f"Categoria: {row[4] or '-'}",
            f"Quantità: {row[5]}",
            f"Prezzo: € {row[6]:.2f}",
            f"Posizione: {row[7] or '-'}",
            f"Valore totale: € {row[5] * row[6]:.2f}",
        ]
        message = " | ".join(details)
        self.set_status(message)

    def _current_row(self) -> Optional[TableRow]:
        if not self.rows or self.selected_index >= len(self.rows):
            return None
        return self.rows[self.selected_index]


def run() -> None:
    """Entry point for running the curses interface."""

    def _main(stdscr: "curses._CursesWindow") -> None:
        curses.curs_set(0)
        stdscr.keypad(True)
        tui = InventoryTUI(stdscr)
        tui.run()

    curses.wrapper(_main)


if __name__ == "__main__":  # pragma: no cover - manual execution
    run()
