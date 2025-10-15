"""Interfaccia grafica completa per la gestione del magazzino."""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Dict, Iterable, List, Optional, Sequence

from inventory_manager import (
    ProductRow,
    add_product,
    calculate_total_value,
    delete_product,
    export_to_csv,
    get_all_products,
    initialize_database,
    update_product,
)


LOW_STOCK_WARNING = 5


def _to_currency(value: float) -> str:
    return f"€ {value:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


class InventoryApp(tk.Tk):
    """Applicazione principale basata su Tkinter."""

    columns: Sequence[str] = (
        "ID",
        "Codice",
        "Nome",
        "Descrizione",
        "Categoria",
        "Quantità",
        "Prezzo",
        "Posizione",
        "Valore",
    )

    def __init__(self) -> None:
        super().__init__()
        self.title("Gestionale di Magazzino")
        self.minsize(1080, 600)

        # Migliora l'usabilità con un menù completo dell'applicazione e
        # scorciatoie da tastiera per le operazioni principali.
        self.option_add("*tearOff", False)
        self._build_menubar()

        self.search_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.sort_column: Optional[str] = None
        self.sort_reverse = False
        self.low_stock_limit: Optional[int] = None
        self.current_rows: List[ProductRow] = []

        self._build_layout()
        self.refresh_table()

    # -- Layout ---------------------------------------------------------
    def _build_menubar(self) -> None:
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar)
        file_menu.add_command(label="Nuovo prodotto", command=self.on_add, accelerator="Ctrl+N")
        file_menu.add_command(label="Modifica selezionato", command=self.on_edit, accelerator="Ctrl+E")
        file_menu.add_command(label="Duplica prodotto", command=self.on_duplicate)
        file_menu.add_command(label="Elimina", command=self.on_delete, accelerator="Canc")
        file_menu.add_separator()
        file_menu.add_command(label="Esporta in CSV", command=self.on_export)
        file_menu.add_separator()
        file_menu.add_command(label="Esci", command=self._on_exit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar)
        view_menu.add_command(label="Aggiorna", command=self.refresh_table, accelerator="F5")
        view_menu.add_command(label="Prodotti sotto scorta...", command=self.on_low_stock)
        view_menu.add_command(label="Pulisci filtri", command=self._clear_filters)
        menubar.add_cascade(label="Visualizza", menu=view_menu)

        help_menu = tk.Menu(menubar)
        help_menu.add_command(label="Scorciatoie", command=self._show_help)
        help_menu.add_separator()
        help_menu.add_command(label="Informazioni", command=self._show_about)
        menubar.add_cascade(label="Aiuto", menu=help_menu)

    def _build_layout(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        toolbar.columnconfigure(3, weight=1)

        ttk.Label(toolbar, text="Cerca").grid(row=0, column=0, sticky="w")
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        self.search_entry.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.search_entry.bind("<Return>", lambda _event: self.refresh_table())

        ttk.Button(toolbar, text="🔍 Cerca", command=self.refresh_table).grid(row=1, column=1, padx=2)
        ttk.Button(toolbar, text="✖ Pulisci", command=self._clear_filters).grid(row=1, column=2, padx=2)

        filters = ttk.Frame(toolbar)
        filters.grid(row=1, column=3, sticky="ew")
        filters.columnconfigure(1, weight=1)
        filters.columnconfigure(3, weight=1)

        ttk.Label(filters, text="Categoria").grid(row=0, column=0, sticky="w")
        self.category_combo = ttk.Combobox(filters, textvariable=self.category_var, state="readonly")
        self.category_combo.grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.category_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_table())

        ttk.Label(filters, text="Posizione").grid(row=0, column=2, sticky="w")
        self.location_combo = ttk.Combobox(filters, textvariable=self.location_var, state="readonly")
        self.location_combo.grid(row=1, column=2, sticky="ew", padx=(0, 6))
        self.location_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_table())

        actions = ttk.Frame(toolbar)
        actions.grid(row=1, column=4, sticky="e")

        ttk.Button(actions, text="➕ Nuovo", command=self.on_add).grid(row=0, column=0, padx=2)
        ttk.Button(actions, text="✏️ Modifica", command=self.on_edit).grid(row=0, column=1, padx=2)
        ttk.Button(actions, text="🗑 Elimina", command=self.on_delete).grid(row=0, column=2, padx=2)
        ttk.Button(actions, text="⬇ Esporta CSV", command=self.on_export).grid(row=0, column=3, padx=2)
        ttk.Button(actions, text="⚠ Sotto scorta", command=self.on_low_stock).grid(row=0, column=4, padx=2)

        # Tabella principale
        table_frame = ttk.Frame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=self.columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=scrollbar_x.set)

        widths = {
            "ID": 70,
            "Codice": 120,
            "Nome": 200,
            "Descrizione": 260,
            "Categoria": 140,
            "Quantità": 110,
            "Prezzo": 110,
            "Posizione": 140,
            "Valore": 140,
        }

        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._toggle_sort(c))
            self.tree.column(col, width=widths.get(col, 120), anchor="w")

        self.tree.bind("<Double-1>", lambda _event: self.on_edit())
        self.tree.bind("<Return>", lambda _event: self.on_edit())
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Button-2>", self._show_context_menu)

        self.tree.tag_configure("low_stock", background="#fff0f0")

        self.tree_menu = tk.Menu(self, tearoff=False)
        self.tree_menu.add_command(label="Apri/Modifica", command=self.on_edit, accelerator="Invio")
        self.tree_menu.add_command(label="Duplica", command=self.on_duplicate)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Nuovo prodotto", command=self.on_add, accelerator="Ctrl+N")
        self.tree_menu.add_command(label="Elimina", command=self.on_delete, accelerator="Canc")

        self.bind_all("<Control-n>", lambda event: self._dispatch_if_enabled(self.on_add, event))
        self.bind_all("<Control-e>", lambda event: self._dispatch_if_enabled(self.on_edit, event))
        self.bind_all("<Delete>", lambda event: self._dispatch_if_enabled(self.on_delete, event))
        self.bind_all("<Control-f>", lambda event: self._focus_search(event))
        self.bind_all("<Control-r>", lambda event: self._dispatch_if_enabled(self._clear_filters, event))
        self.bind_all("<Control-q>", lambda event: self._dispatch_if_enabled(self._on_exit, event))
        self.bind_all("<F5>", lambda event: self._dispatch_if_enabled(self.refresh_table, event))

        self.status_var = tk.StringVar()
        status = ttk.Label(self, textvariable=self.status_var, anchor="w", relief="sunken")
        status.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

    # -- Azioni ---------------------------------------------------------
    def _clear_filters(self) -> None:
        self.search_var.set("")
        self.category_var.set("")
        self.location_var.set("")
        self.low_stock_limit = None
        self.refresh_table()

    def _dispatch_if_enabled(self, callback, event: Optional[tk.Event]) -> str:
        del event  # non usato, ma mantenuto per compatibilità con bind_all
        callback()
        return "break"

    def _focus_search(self, _event: Optional[tk.Event]) -> str:
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)
        return "break"

    def _show_context_menu(self, event: tk.Event) -> str:
        iid = self.tree.identify_row(event.y)
        if iid:
            self.tree.selection_set(iid)
            self.tree.focus(iid)
        try:
            self.tree_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.tree_menu.grab_release()
        return "break"

    def _on_exit(self) -> None:
        if messagebox.askokcancel("Esci", "Vuoi chiudere il gestionale?"):
            self.destroy()

    def _show_help(self) -> None:
        message = (
            "Scorciatoie disponibili:\n\n"
            "Ctrl+N: nuovo prodotto\n"
            "Ctrl+E o Invio: modifica il prodotto selezionato\n"
            "Ctrl+F: attiva la ricerca rapida\n"
            "Ctrl+R: pulisce tutti i filtri\n"
            "F5: aggiorna l'elenco\n"
            "Canc: elimina il prodotto selezionato\n"
            "Ctrl+Q: chiude l'applicazione"
        )
        messagebox.showinfo("Guida rapida", message, parent=self)

    def _show_about(self) -> None:
        messagebox.showinfo(
            "Informazioni",
            "Gestionale di magazzino\nVersione Tkinter ottimizzata per l'uso con mouse e menu a tendina.",
            parent=self,
        )

    def _toggle_sort(self, column: str) -> None:
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh_table()

    def _filter_rows(self, rows: Iterable[ProductRow]) -> List[ProductRow]:
        result = list(rows)
        if self.low_stock_limit is not None:
            result = [row for row in result if row[5] <= self.low_stock_limit]

        term = self.search_var.get().strip().lower()
        if term:
            result = [row for row in result if term in row[1].lower() or term in row[2].lower()]

        category = self.category_var.get()
        if category:
            result = [row for row in result if row[4] == category]

        location = self.location_var.get()
        if location:
            result = [row for row in result if row[7] == location]

        if self.sort_column:
            index_map: Dict[str, int] = {name: idx for idx, name in enumerate(self.columns)}
            idx = index_map[self.sort_column]
            result.sort(key=lambda item: item[idx], reverse=self.sort_reverse)

        return result

    def refresh_table(self) -> None:
        initialize_database()
        all_rows = get_all_products()
        rows = self._filter_rows(all_rows)

        for child in self.tree.get_children():
            self.tree.delete(child)

        categories = sorted({row[4] for row in all_rows if row[4]})
        locations = sorted({row[7] for row in all_rows if row[7]})

        self.category_combo["values"] = [""] + categories
        self.location_combo["values"] = [""] + locations

        if self.category_var.get() not in categories:
            self.category_var.set("")
        if self.location_var.get() not in locations:
            self.location_var.set("")

        self.current_rows = rows
        for row in rows:
            product_id, code, name, description, category, quantity, price, location = row
            value = quantity * price
            tags = ("low_stock",) if quantity <= LOW_STOCK_WARNING else ()
            self.tree.insert(
                "",
                "end",
                iid=str(product_id),
                values=(
                    product_id,
                    code,
                    name,
                    description,
                    category,
                    quantity,
                    f"{price:.2f}",
                    location,
                    f"{value:.2f}",
                ),
                tags=tags,
            )

        filtered_value = sum(row[5] * row[6] for row in rows)
        total_value = calculate_total_value()
        self.status_var.set(
            "Prodotti visualizzati: "
            f"{len(rows)} | Valore visualizzato: {_to_currency(filtered_value)} | Valore totale: {_to_currency(total_value)}"
        )

    def _get_selected_product(self) -> Optional[ProductRow]:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Selezione richiesta", "Seleziona un prodotto dalla tabella.")
            return None
        product_id = int(selected[0])
        for row in self.current_rows:
            if row[0] == product_id:
                return row
        return None

    def on_add(self) -> None:
        dialog = ProductDialog(self, title="Nuovo prodotto")
        product = dialog.show()
        if product is None:
            return
        try:
            add_product(**product)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Errore", str(exc))
            return
        self.refresh_table()

    def on_edit(self) -> None:
        row = self._get_selected_product()
        if row is None:
            return

        dialog = ProductDialog(
            self,
            title="Modifica prodotto",
            initial=ProductData(
                code=row[1],
                name=row[2],
                description=row[3],
                category=row[4],
                quantity=row[5],
                price=row[6],
                location=row[7],
            ),
            editing=True,
        )
        product = dialog.show()
        if product is None:
            return
        try:
            updated = update_product(
                row[0],
                name=product["name"],
                description=product["description"],
                category=product["category"],
                quantity=product["quantity"],
                price=product["price"],
                location=product["location"],
            )
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Errore", str(exc))
            return
        if not updated:
            messagebox.showwarning("Non trovato", "Il prodotto selezionato non esiste più in archivio.")
        self.refresh_table()

    def on_duplicate(self) -> None:
        row = self._get_selected_product()
        if row is None:
            return

        dialog = ProductDialog(
            self,
            title="Duplica prodotto",
            initial=ProductData(
                code=f"{row[1]}-copy",
                name=row[2],
                description=row[3],
                category=row[4],
                quantity=row[5],
                price=row[6],
                location=row[7],
            ),
        )
        product = dialog.show()
        if product is None:
            return
        try:
            add_product(**product)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Errore", str(exc))
            return
        self.refresh_table()

    def on_delete(self) -> None:
        row = self._get_selected_product()
        if row is None:
            return
        if not messagebox.askyesno(
            "Conferma eliminazione",
            f"Vuoi eliminare definitivamente '{row[2]}' (codice {row[1]})?",
            icon=messagebox.WARNING,
        ):
            return
        try:
            delete_product(row[0])
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Errore", str(exc))
            return
        self.refresh_table()

    def on_export(self) -> None:
        filepath = filedialog.asksaveasfilename(
            title="Esporta inventario in CSV",
            defaultextension=".csv",
            filetypes=[("File CSV", "*.csv"), ("Tutti i file", "*.*")],
        )
        if not filepath:
            return
        try:
            export_to_csv(filepath)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Errore", str(exc))
            return
        messagebox.showinfo("Esportazione completata", f"File salvato in:\n{filepath}")

    def on_low_stock(self) -> None:
        threshold = simpledialog.askinteger(
            "Prodotti sotto scorta",
            "Mostra gli articoli con quantità minore o uguale a...",
            parent=self,
            minvalue=0,
        )
        if threshold is None:
            return
        self.low_stock_limit = threshold
        self.refresh_table()


@dataclass
class ProductData:
    code: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    quantity: int = 0
    price: float = 0.0
    location: str = ""


class ProductDialog(tk.Toplevel):
    """Finestra di dialogo per inserire o modificare un prodotto."""

    def __init__(
        self,
        master: tk.Tk,
        *,
        title: str,
        initial: Optional[ProductData] = None,
        editing: bool = False,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)

        self.result: Optional[Dict[str, object]] = None
        data = initial or ProductData()

        frame = ttk.Frame(self, padding=12)
        frame.grid(row=0, column=0)

        price_value = f"{data.price:.2f}" if editing or data.price else ""

        fields = [
            ("Codice", "code", data.code, not editing),
            ("Nome", "name", data.name, True),
            ("Descrizione", "description", data.description, True),
            ("Categoria", "category", data.category, True),
            ("Quantità", "quantity", str(data.quantity), True),
            ("Prezzo", "price", price_value, True),
            ("Posizione", "location", data.location, True),
        ]

        self.entries: Dict[str, tk.Entry] = {}
        for idx, (label, key, value, enabled) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=idx, column=0, sticky="e", pady=3)
            entry = ttk.Entry(frame)
            entry.grid(row=idx, column=1, sticky="ew", pady=3)
            entry.insert(0, value)
            if not enabled:
                entry.state(["disabled"])
            self.entries[key] = entry

        frame.columnconfigure(1, weight=1)

        buttons = ttk.Frame(frame)
        buttons.grid(row=len(fields), column=0, columnspan=2, pady=(12, 0))

        ttk.Button(buttons, text="Annulla", command=self._on_cancel).grid(row=0, column=0, padx=4)
        ttk.Button(buttons, text="Salva", command=self._on_save).grid(row=0, column=1, padx=4)

        self.bind("<Return>", lambda _event: self._on_save())
        self.bind("<Escape>", lambda _event: self._on_cancel())

    def show(self) -> Optional[Dict[str, object]]:
        self.wait_window(self)
        return self.result

    def _on_save(self) -> None:
        try:
            data = ProductData(
                code=self.entries["code"].get().strip(),
                name=self.entries["name"].get().strip(),
                description=self.entries["description"].get().strip(),
                category=self.entries["category"].get().strip(),
                quantity=int(self.entries["quantity"].get().strip() or 0),
                price=float(self.entries["price"].get().replace(",", ".") or 0.0),
                location=self.entries["location"].get().strip(),
            )
        except ValueError:
            messagebox.showerror("Valori non validi", "Inserisci numeri corretti per quantità e prezzo.")
            return

        if not data.code or not data.name:
            messagebox.showerror("Campi obbligatori", "Codice e nome sono obbligatori.")
            return

        self.result = {
            "code": data.code,
            "name": data.name,
            "description": data.description,
            "category": data.category,
            "quantity": data.quantity,
            "price": data.price,
            "location": data.location,
        }
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()


def run() -> None:
    initialize_database()
    app = InventoryApp()
    app.mainloop()


if __name__ == "__main__":
    run()
