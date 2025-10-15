# Gestionale di magazzino (CLI Python)

Questo progetto fornisce un gestionale di magazzino completo con tre
interfacce: menu testuale classico, tabella navigabile in stile foglio di
calcolo e nuova GUI moderna basata su Tkinter. I dati sono salvati in un
database SQLite (`inventory.db`) e l'app consente di aggiungere, modificare,
cercare, filtrare, visualizzare ed esportare i prodotti presenti in inventario.

## Requisiti

- Python 3.8 o superiore
- Nessuna dipendenza esterna su Linux/macOS; su Windows installare anche `windows-curses` per usare la TUI

## Avvio rapido

1. (Opzionale) Creare ed attivare un ambiente virtuale:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Su Windows usare `.venv\Scripts\activate`
   ```

2. Installare il supporto opzionale per la TUI su Windows:

   ```bash
   python -m pip install windows-curses
   ```

3. Avviare il programma (di default verrà caricata direttamente la GUI a
   finestre):

   ```bash
   python app.py
   ```

   Per selezionare una diversa interfaccia è possibile indicarla esplicitamente
   tramite opzione:

   ```bash
   python app.py --interface cli  # oppure tui / gui
   ```

   Su Windows è inoltre possibile avviare la versione grafica senza finestra
   console facendo doppio clic su `start_gui.pyw` oppure sul collegamento
   `menu_launcher.bat`, che proverà prima la GUI e in caso di errore ripiegherà
   sull'interfaccia testuale.

In alternativa è possibile avviare direttamente una delle interfacce:

```bash
# Interfaccia classica a menu testuale
python inventory_manager.py

# Interfaccia navigabile stile foglio di calcolo
python inventory_tui.py

# Interfaccia grafica moderna basata su Tkinter (menu a tendina, scorciatoie)
python inventory_gui.py
```

Al primo avvio verrà creato automaticamente il database `inventory.db` nella
stessa cartella dello script.

## Interfaccia grafica dedicata

La GUI (`inventory_gui.py`) offre una vista completa con barra degli strumenti,
menu a tendina nello stile delle applicazioni desktop e menu contestuale sul
click destro. È possibile utilizzare scorciatoie da tastiera (Ctrl+N per un
nuovo articolo, Ctrl+E o Invio per modificarlo, F5 per aggiornare la lista,
Ctrl+F per focalizzare la ricerca, Canc per eliminare, Ctrl+Q per chiudere) e
duplicare rapidamente un prodotto esistente. I filtri per categoria e posizione
sono disponibili tramite le combo dedicate e la voce "Visualizza" della barra
dei menu.

## Interfaccia a tabella

Il file `inventory_tui.py` fornisce un'interfaccia curses che presenta
l'inventario in una tabella navigabile con tastiera e mouse. Le frecce permettono
di scorrere le righe, mentre i comandi mostrati nel piè di pagina consentono di
aggiungere, modificare, filtrare ed esportare i dati senza uscire dalla vista
principale. L'interfaccia ricorda l'esperienza di consultazione tipica dei
fogli di calcolo pur rimanendo interamente in ambiente terminale.

## Funzionalità principali

- **Aggiungi prodotto**: inserisce un nuovo articolo con codice univoco,
  nome, descrizione, categoria, quantità, prezzo unitario e posizione fisica.
- **Visualizza inventario**: mostra una tabella riepilogativa con possibilità
  di ordinare per codice, nome, quantità, prezzo, categoria o posizione.
- **Aggiorna prodotto**: consente di modificare qualsiasi campo di un
  articolo esistente selezionandolo tramite ID.
- **Elimina prodotto**: rimuove un articolo dal database.
- **Ricerca**: filtra gli articoli per codice o nome con supporto
  all'ordinamento.
- **Filtri**: permette di visualizzare solo gli articoli di una certa
  categoria o collocazione.
- **Controllo scorte**: individua gli articoli la cui quantità è inferiore o
  uguale ad una soglia definita dall'utente.
- **Valore totale**: calcola il valore economico complessivo dell'inventario.
- **Esportazione CSV**: crea un file CSV con tutti i dati, comprensivo del
  valore totale (quantità × prezzo) per ogni articolo.

## Struttura del database

La tabella `products` viene creata automaticamente con i seguenti campi:

- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `code` (TEXT UNIQUE)
- `name` (TEXT NOT NULL)
- `description` (TEXT)
- `category` (TEXT)
- `quantity` (INTEGER NOT NULL)
- `price` (REAL NOT NULL)
- `location` (TEXT)

## Suggerimenti d'uso

- Utilizzare il campo "ID" mostrato nella tabella dell'inventario per
  aggiornare o eliminare rapidamente gli articoli.
- Per importi con decimali è possibile usare sia il punto che la virgola.
- I file CSV esportati sono salvati nella cartella corrente e possono essere
  aperti con qualsiasi editor di testo o software per fogli di calcolo.

## Miglioramenti futuri

Possibili estensioni comprendono il supporto multiutente con autenticazione,
una sezione dedicata ai fornitori e agli ordini, l'esportazione in formato
Excel/PDF e un sistema di notifiche automatiche per le scorte critiche.
