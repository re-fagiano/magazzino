"""Inventory management CLI application backed by SQLite.

This module provides functions to manage a local warehouse inventory using
an SQLite database stored in the current working directory.  It implements
CRUD operations, searching, filtering, reporting, and CSV export features
exposed via a simple command-line interface.
"""

from __future__ import annotations

import csv
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

DB_NAME = "inventory.db"


ProductRow = Tuple[int, str, str, str, str, int, float, str]


def connect_db() -> sqlite3.Connection:
    """Return a connection to the SQLite database located in the project directory."""

    return sqlite3.connect(DB_NAME)


def initialize_database() -> None:
    """Create the products table if it does not exist."""

    with connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                location TEXT
            )
            """
        )
        conn.commit()


def _validate_quantity(quantity: int) -> None:
    if quantity < 0:
        raise ValueError("La quantità deve essere un intero maggiore o uguale a zero.")


def _validate_price(price: float) -> None:
    if price < 0:
        raise ValueError("Il prezzo deve essere un numero maggiore o uguale a zero.")


def add_product(
    code: str,
    name: str,
    description: str,
    category: str,
    quantity: int,
    price: float,
    location: str,
) -> None:
    """Insert a new product into the database, ensuring unique product codes."""

    _validate_quantity(quantity)
    _validate_price(price)

    with connect_db() as conn:
        try:
            conn.execute(
                """
                INSERT INTO products (code, name, description, category, quantity, price, location)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (code, name.strip(), description.strip(), category.strip(), quantity, price, location.strip()),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:  # raised when code violates UNIQUE constraint
            raise ValueError(
                f"Impossibile aggiungere il prodotto: esiste già un elemento con codice '{code}'."
            ) from exc


ORDERABLE_COLUMNS = {"id", "code", "name", "quantity", "price", "category", "location"}


def _build_order_clause(order_by: Optional[str], descending: bool) -> str:
    if not order_by:
        return ""
    order_by = order_by.lower()
    if order_by not in ORDERABLE_COLUMNS:
        raise ValueError(
            f"Campo di ordinamento non valido. Scegli tra: {', '.join(sorted(ORDERABLE_COLUMNS))}."
        )
    direction = "DESC" if descending else "ASC"
    return f" ORDER BY {order_by} {direction}"


def get_all_products(order_by: Optional[str] = None, descending: bool = False) -> List[ProductRow]:
    """Return all products, optionally sorted by a column."""

    query = "SELECT id, code, name, description, category, quantity, price, location FROM products"
    query += _build_order_clause(order_by, descending)
    with connect_db() as conn, closing(conn.cursor()) as cur:
        cur.execute(query)
        return list(cur.fetchall())


def update_product(
    product_id: int,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    location: Optional[str] = None,
) -> bool:
    """Update an existing product with the provided fields.

    Returns True if a product was updated, False if the product ID does not exist.
    """

    updates = []
    params: List[object] = []

    if name is not None:
        updates.append("name = ?")
        params.append(name.strip())
    if description is not None:
        updates.append("description = ?")
        params.append(description.strip())
    if category is not None:
        updates.append("category = ?")
        params.append(category.strip())
    if quantity is not None:
        _validate_quantity(quantity)
        updates.append("quantity = ?")
        params.append(quantity)
    if price is not None:
        _validate_price(price)
        updates.append("price = ?")
        params.append(price)
    if location is not None:
        updates.append("location = ?")
        params.append(location.strip())

    if not updates:
        raise ValueError("Nessun campo da aggiornare fornito.")

    params.append(product_id)

    with connect_db() as conn:
        cur = conn.execute(
            f"UPDATE products SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        conn.commit()
        return cur.rowcount > 0


def delete_product(product_id: int) -> bool:
    """Delete a product by ID. Returns True if the product existed."""

    with connect_db() as conn:
        cur = conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
        return cur.rowcount > 0


def search_products(
    term: str,
    order_by: Optional[str] = None,
    descending: bool = False,
) -> List[ProductRow]:
    """Search products whose code or name contains the given term."""

    wildcard_term = f"%{term.strip()}%"
    query = (
        "SELECT id, code, name, description, category, quantity, price, location "
        "FROM products WHERE code LIKE ? OR name LIKE ?"
    )
    query += _build_order_clause(order_by, descending)

    with connect_db() as conn, closing(conn.cursor()) as cur:
        cur.execute(query, (wildcard_term, wildcard_term))
        return list(cur.fetchall())


def filter_by_category(
    category: str,
    order_by: Optional[str] = None,
    descending: bool = False,
) -> List[ProductRow]:
    """Return all products belonging to a specific category."""

    query = "SELECT id, code, name, description, category, quantity, price, location FROM products WHERE category = ?"
    query += _build_order_clause(order_by, descending)
    with connect_db() as conn, closing(conn.cursor()) as cur:
        cur.execute(query, (category.strip(),))
        return list(cur.fetchall())


def filter_by_location(
    location: str,
    order_by: Optional[str] = None,
    descending: bool = False,
) -> List[ProductRow]:
    """Return all products stored in the specified location."""

    query = "SELECT id, code, name, description, category, quantity, price, location FROM products WHERE location = ?"
    query += _build_order_clause(order_by, descending)
    with connect_db() as conn, closing(conn.cursor()) as cur:
        cur.execute(query, (location.strip(),))
        return list(cur.fetchall())


def get_low_stock_items(threshold: int) -> List[ProductRow]:
    """Return products whose quantity is less than or equal to the provided threshold."""

    if threshold < 0:
        raise ValueError("La soglia minima non può essere negativa.")

    query = (
        "SELECT id, code, name, description, category, quantity, price, location "
        "FROM products WHERE quantity <= ?"
    )
    with connect_db() as conn, closing(conn.cursor()) as cur:
        cur.execute(query, (threshold,))
        return list(cur.fetchall())


def calculate_total_value() -> float:
    """Return the total value of the inventory (sum of quantity * price)."""

    with connect_db() as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT COALESCE(SUM(quantity * price), 0) FROM products")
        (total_value,) = cur.fetchone()
        return float(total_value or 0.0)


def export_to_csv(filename: Optional[str] = None) -> str:
    """Export the inventory to a CSV file and return the file path."""

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inventory_export_{timestamp}.csv"

    products = get_all_products()
    headers = [
        "ID",
        "Codice",
        "Nome",
        "Descrizione",
        "Categoria",
        "Quantità",
        "Prezzo",
        "Posizione",
        "Valore Totale",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        for product in products:
            value_total = product[5] * product[6]
            writer.writerow([*product, value_total])

    return os.path.abspath(filename)


def _format_products_table(products: Sequence[ProductRow]) -> str:
    """Return a string table representation of product rows."""

    if not products:
        return "Nessun prodotto trovato."

    headers = [
        "ID",
        "Codice",
        "Nome",
        "Descrizione",
        "Categoria",
        "Quantità",
        "Prezzo",
        "Posizione",
        "Valore Totale",
    ]

    rows: List[Sequence[object]] = [
        [
            prod[0],
            prod[1],
            prod[2],
            prod[3],
            prod[4],
            prod[5],
            f"{prod[6]:.2f}",
            prod[7],
            f"{prod[5] * prod[6]:.2f}",
        ]
        for prod in products
    ]
    widths = [len(header) for header in headers]

    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))

    def format_row(row: Sequence[object]) -> str:
        return " | ".join(str(cell).ljust(widths[idx]) for idx, cell in enumerate(row))

    separator = "-+-".join("-" * width for width in widths)
    table_lines = [format_row(headers), separator]
    table_lines.extend(format_row(row) for row in rows)
    return "\n".join(table_lines)


def _prompt_for_sorting() -> Tuple[Optional[str], bool]:
    print("\nCampi ordinabili: id, code, name, quantity, price, category, location")
    order_field = input("Campo per l'ordinamento (lascia vuoto per nessuno): ").strip() or None
    if order_field:
        descending_input = input("Ordinamento decrescente? (s/N): ").strip().lower()
        descending = descending_input == "s"
    else:
        descending = False
    return order_field, descending


def _prompt_for_product_id() -> int:
    while True:
        try:
            return int(input("Inserisci l'ID del prodotto: ").strip())
        except ValueError:
            print("ID non valido. Inserisci un numero intero.")


def _prompt_for_quantity(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt).strip())
            _validate_quantity(value)
            return value
        except ValueError as exc:
            print(exc)


def _prompt_for_price(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt).strip().replace(",", "."))
            _validate_price(value)
            return value
        except ValueError as exc:
            print(exc)


def _cli_add_product() -> None:
    print("\n=== Aggiungi prodotto ===")
    code = input("Codice: ").strip()
    name = input("Nome: ").strip()
    description = input("Descrizione: ").strip()
    category = input("Categoria: ").strip()
    quantity = _prompt_for_quantity("Quantità: ")
    price = _prompt_for_price("Prezzo unitario: ")
    location = input("Posizione (corsia/scaffale): ").strip()

    try:
        add_product(code, name, description, category, quantity, price, location)
        print("Prodotto aggiunto correttamente.")
    except ValueError as exc:
        print(f"Errore: {exc}")


def _cli_view_products() -> None:
    print("\n=== Inventario ===")
    order_field, descending = _prompt_for_sorting()
    try:
        products = get_all_products(order_field, descending)
        print(_format_products_table(products))
    except ValueError as exc:
        print(f"Errore: {exc}")


def _cli_update_product() -> None:
    print("\n=== Aggiorna prodotto ===")
    product_id = _prompt_for_product_id()
    print("Lascia vuoto un campo per non modificarlo.")
    name = input("Nuovo nome: ").strip() or None
    description = input("Nuova descrizione: ").strip() or None
    category = input("Nuova categoria: ").strip() or None

    quantity_input = input("Nuova quantità: ").strip()
    quantity = None
    if quantity_input:
        try:
            quantity = int(quantity_input)
            _validate_quantity(quantity)
        except ValueError as exc:
            print(f"Errore: {exc}")
            return

    price_input = input("Nuovo prezzo unitario: ").strip().replace(",", ".")
    price = None
    if price_input:
        try:
            price = float(price_input)
            _validate_price(price)
        except ValueError as exc:
            print(f"Errore: {exc}")
            return

    location = input("Nuova posizione: ").strip() or None

    try:
        updated = update_product(
            product_id,
            name=name,
            description=description,
            category=category,
            quantity=quantity,
            price=price,
            location=location,
        )
    except ValueError as exc:
        print(f"Errore: {exc}")
        return

    if updated:
        print("Prodotto aggiornato correttamente.")
    else:
        print("Nessun prodotto trovato con l'ID fornito.")


def _cli_delete_product() -> None:
    print("\n=== Elimina prodotto ===")
    product_id = _prompt_for_product_id()
    if delete_product(product_id):
        print("Prodotto eliminato.")
    else:
        print("Nessun prodotto trovato con l'ID fornito.")


def _cli_search_products() -> None:
    print("\n=== Ricerca prodotti ===")
    term = input("Termine di ricerca (nome o codice): ").strip()
    order_field, descending = _prompt_for_sorting()
    try:
        products = search_products(term, order_field, descending)
        print(_format_products_table(products))
    except ValueError as exc:
        print(f"Errore: {exc}")


def _cli_filter_category() -> None:
    print("\n=== Filtra per categoria ===")
    category = input("Categoria: ").strip()
    order_field, descending = _prompt_for_sorting()
    try:
        products = filter_by_category(category, order_field, descending)
        print(_format_products_table(products))
    except ValueError as exc:
        print(f"Errore: {exc}")


def _cli_filter_location() -> None:
    print("\n=== Filtra per posizione ===")
    location = input("Posizione: ").strip()
    order_field, descending = _prompt_for_sorting()
    try:
        products = filter_by_location(location, order_field, descending)
        print(_format_products_table(products))
    except ValueError as exc:
        print(f"Errore: {exc}")


def _cli_low_stock_alert() -> None:
    print("\n=== Controllo scorte basse ===")
    threshold = _prompt_for_quantity("Soglia minima: ")
    low_stock_items = get_low_stock_items(threshold)
    if low_stock_items:
        print("Attenzione! I seguenti prodotti sono sotto la soglia:")
        print(_format_products_table(low_stock_items))
    else:
        print("Nessun prodotto sotto la soglia specificata.")


def _cli_total_value() -> None:
    print("\n=== Valore totale dell'inventario ===")
    total = calculate_total_value()
    print(f"Valore complessivo: € {total:.2f}")


def _cli_export_csv() -> None:
    print("\n=== Esportazione CSV ===")
    filename = input("Nome file CSV (lascia vuoto per default): ").strip() or None
    filepath = export_to_csv(filename)
    print(f"Inventario esportato in: {filepath}")


MENU_OPTIONS = {
    "1": ("Aggiungi prodotto", _cli_add_product),
    "2": ("Visualizza inventario", _cli_view_products),
    "3": ("Aggiorna prodotto", _cli_update_product),
    "4": ("Elimina prodotto", _cli_delete_product),
    "5": ("Cerca prodotti", _cli_search_products),
    "6": ("Filtra per categoria", _cli_filter_category),
    "7": ("Filtra per posizione", _cli_filter_location),
    "8": ("Mostra prodotti sotto soglia", _cli_low_stock_alert),
    "9": ("Calcola valore totale", _cli_total_value),
    "10": ("Esporta inventario in CSV", _cli_export_csv),
}


def display_menu() -> None:
    """Print the available menu options."""

    print("\n============================")
    print(" Gestione Magazzino - Menu")
    print("============================")
    for key, (label, _) in MENU_OPTIONS.items():
        print(f" {key}. {label}")
    print(" 0. Esci")


def main() -> None:
    """Run the CLI loop until the user chooses to exit."""

    initialize_database()
    while True:
        display_menu()
        choice = input("\nSeleziona un'opzione: ").strip()
        if choice == "0":
            print("Uscita dal programma. A presto!")
            break
        action = MENU_OPTIONS.get(choice)
        if action:
            _, handler = action
            handler()
        else:
            print("Opzione non valida. Riprova.")


if __name__ == "__main__":
    main()
