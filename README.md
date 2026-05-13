# 🏐 Volleyball Scout

App professionale di scouting pallavolo con sincronizzazione video e export DataVolley (.dvw).

---

## 📚 Documentazione

Tutta la documentazione è organizzata in [`docs/`](docs/):

```
docs/
├── overview/          # Panoramica, architettura, riepiloghi
├── setup/             # Quick start, lancio, accelerazione hardware
├── login/             # Sistema di autenticazione
├── database/          # Gestione database, strumenti DB
├── formations/        # Gestione formazioni e setup
├── team-players/      # Gestione giocatori e squadre
├── matches/           # Gestione partite
├── theme/             # Tema scuro, UI, changelog
├── assets/            # Asset e deployment
├── video/             # Acquisizione e sorgenti video
├── detection/         # Rilevamento e configurazione detector
├── ui/                # Architettura e guida UI
├── scouting/          # Flusso di scouting
├── implementation/    # Dettagli implementativi e migrazioni
├── testing/           # Test e documentazione QA
├── navigation/        # Strumenti e navigazione
└── analysis/          # Analisi e progressi
```

→ Vedi [`docs/INDEX.md`](docs/INDEX.md) per l'indice completo di navigazione.

## 🚀 Avvio rapido

```bash
python setup.py dev_setup
python main.py
```

## 📁 Struttura del codice

```
├── src/                # Codice sorgente principale
├── volleyball_scout/   # Package principale app
├── scripts/            # Script di utilità
├── tests/              # Test automatici
├── data/               # Dati (keypoint, config)
├── alembic/            # Migrazioni database
├── config/             # Configurazione
├── output/             # Output generati
├── runs/               # Run di esecuzione
├── docs/               # Documentazione (questa cartella)
├── venv/               # Ambiente virtuale
├── yolov8n*.pt         # Modelli YOLOv8
├── main.py             # Entry point
├── run_desktop.py      # Lancio desktop
└── setup.py            # Setup e dipendenze
```

## 📋 Licenza

[MIT License](LICENSE)