# Gestionale di magazzino (CLI Python)

Questo progetto fornisce una semplice applicazione da riga di comando per la
gestione di un magazzino locale. I dati sono salvati in un database SQLite
(`inventory.db`) e l'app consente di aggiungere, modificare, cercare, filtrare,
visualizzare ed esportare i prodotti presenti in inventario.

## Requisiti

- Python 3.8 o superiore
- Nessuna dipendenza esterna su Linux/macOS; su Windows installare anche `windows-curses` per usare la TUI

## Avvio rapido

1. (Opzionale) Creare ed attivare un ambiente virtuale:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Su Windows usare `.venv\Scripts\activate`
   ```

2. Installare il supporto opzionale per la TUI su Windows (senza di esso il
   launcher mostrerà un messaggio di errore e tornerà al menu classico):

   ```bash
   # Necessario solo su Windows per abilitare il modulo curses
   pip install windows-curses
   ```

3. Avviare il programma da terminale e scegliere l'interfaccia desiderata:

   ```bash
   python app.py
   ```

   Verrà mostrato un piccolo menu iniziale che permette di accedere sia alla
   versione classica a menu sia alla nuova interfaccia navigabile stile foglio
   di calcolo.

In alternativa è possibile avviare direttamente una delle due interfacce:

```bash
# Interfaccia classica a menu testuale
python inventory_manager.py

# Interfaccia navigabile stile foglio di calcolo
python inventory_tui.py
```

Al primo avvio verrà creato automaticamente il database `inventory.db` nella
stessa cartella dello script.

## Interfaccia a tabella

Il file `inventory_tui.py` fornisce un'interfaccia curses che presenta
l'inventario in una tabella navigabile con tastiera. Le frecce permettono di
scorrere le righe, mentre i comandi mostrati nel piè di pagina consentono di
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

Possibili estensioni comprendono una GUI con Tkinter, la gestione dei
fornitori, l'esportazione in formato Excel o PDF, e la generazione di avvisi
via email per le scorte basse.
