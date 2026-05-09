# 🚀 Quick Start - Squadre e Giocatori

## Accesso Rapido

Dalla finestra principale, vai al menu:
```
👁️ Visualizza → 👥 Squadre e Giocatori
```

oppure clicca sulla card della dashboard.

---

## Layout

La pagina è divisa in due sezioni:

```
┌─ 25% ─────────────────┬─ 75% ─────────────────────────────────────┐
│  LISTA SQUADRE        │  DETTAGLI SQUADRA + LISTA GIOCATORI       │
│                       │                                             │
│  🏐 Team Alpha        │  Nome: Team Alpha                          │
│  🏐 Team Beta         │  Abbrev: TA                                │
│  🏐 Team Gamma        │  Categoria: Serie A1                       │
│                       │  Impianto: PalaComunale                    │
│                       │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ [Trascinare per       │  ➕ Aggiungi Giocatore | ❌ Rimuovi       │
│  ridimensionare]      │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                       │  #01 - Mario Rossi (Palleggiatore)         │
│                       │  #10 - Lucia Bianchi (Schiacciatore)       │
│                       │  #12 - Paolo Verdi (Centrale)              │
│                       │  ✅ Salva Squadra | ❌ Elimina | ↩️ Ann. │
│                       │                                             │
└───────────────────────┴─────────────────────────────────────────────┘
```

---

## Operazioni Principali

### 1️⃣ Aggiungere una Squadra

1. Clicca **"➕ Aggiungi Squadra"** (in alto a destra)
2. Compila il form:
   - **Nome**: (obbligatorio)
   - **Abbreviazione**: (es. "TA")
   - **Categoria**: (es. "Serie A1")
   - **Impianto**: (es. "PalaComunale")
   - **Logo**: (opzionale) - clicca 🖼️ Scegli Logo
3. Clicca **"✅ Salva Squadra"**

### 2️⃣ Selezionare una Squadra

1. Clicca sul nome della squadra nel sidebar sinistro
2. La squadra si espande a destra con i suoi dettagli e giocatori

### 3️⃣ Aggiungere un Giocatore

1. Seleziona una squadra
2. Clicca **"➕ Aggiungi Giocatore"**
3. Si apre il dialog "Nuovo Giocatore"
4. Compila:
   - **Nome**: (facoltativo, es. "Mario")
   - **Cognome**: 🔴 OBBLIGATORIO (es. "Rossi")
   - **Numero Maglia**: 0-99 (es. "01")
   - **Ruolo**: Seleziona dal dropdown:
     - Palleggiatore
     - Opposto
     - Schiacciatore
     - Centrale
     - Libero
   - **Foto**: (opzionale) - clicca 📷 Scegli Foto
5. Clicca **"✅ Salva"**

### 4️⃣ Modificare un Giocatore

**Metodo 1: Doppio-click**
1. **Doppio-click** direttamente sul giocatore nella lista
2. Si apre il dialog "Modifica Giocatore"
3. Modifica i campi desiderati
4. Clicca **"✅ Salva"**

**Metodo 2: Pulsante Modifica**
1. Seleziona il giocatore (singolo click)
2. Clicca il pulsante di modifica (se disponibile)
3. Modifica e salva

### 5️⃣ Eliminare un Giocatore

1. Seleziona il giocatore nella lista
2. Clicca **"❌ Rimuovi Giocatore"**
3. Conferma l'eliminazione nel dialog
4. Il giocatore viene rimosso

### 6️⃣ Eliminare una Squadra

1. Seleziona la squadra (se necessario modificarla prima)
2. Clicca **"❌ Elimina Squadra"**
3. Conferma l'eliminazione
4. ⚠️ Tutti i giocatori della squadra verranno eliminati

---

## 🔄 Dialog di Modifica Dettaglio

Quando apri il dialog per modificare/aggiungere un giocatore:

```
┌─────────────────────────────────────────┐
│  Modifica Giocatore / Nuovo Giocatore   │
├─────────────────────────────────────────┤
│                                         │
│  Nome:                    [____________]│
│  Cognome:                 [____________]│
│  Numero Maglia:           [  01  ]     │
│  Ruolo:                   [▼ Palleggiatore]
│  Foto:                    [📷 ...] [📷 Scegli]
│                                         │
│           ✅ Salva    ❌ Annulla        │
│                                         │
└─────────────────────────────────────────┘
```

### Validazione:
- ❌ **Cognome vuoto** → Errore: "Il cognome è obbligatorio"
- ❌ **Numero fuori range** → Errore: "Il numero maglia deve essere 0-99"
- ❌ **Ruolo non selezionato** → Errore: "Seleziona un ruolo"
- ✅ **Nome facoltativo** → Può essere vuoto
- ✅ **Foto facoltativa** → Può essere saltata

---

## 💡 Tips & Tricks

| Cosa | Come | Perché |
|------|------|--------|
| Ingrandire sidebar | Trascinare il divisore verso destra | Più spazio per squadre |
| Numero maglia padded | Usa `01`, `10`, non `1`, `10` | Migliore ordinamento |
| Cercare giocatore | Clicca sulla lista e inizia a digitare | Ricerca incrementale |
| Annullare modifica | Clicca ❌ Annulla | Non salva i cambiamenti |
| Reset form | Clicca ↩️ Annulla | Torna alla visualizzazione |

---

## ⚠️ Errori Comuni

### Errore: "Seleziona una squadra"
**Soluzione**: Clicca una squadra nel sidebar sinistra prima di aggiungere un giocatore

### Errore: "Il cognome è obbligatorio"
**Soluzione**: Compila il campo "Cognome" nel dialog

### Errore: "Il numero maglia deve essere tra 0 e 99"
**Soluzione**: Inserisci un numero tra 0 e 99 nel campo "Numero Maglia"

### Foto non si salva
**Soluzione**: Assicurati che il file sia:
- Un'immagine valida (PNG, JPG, JPEG, BMP)
- Non corrotta
- Nel percorso accessibile

---

## 🎨 Colori & Tema

- 🌙 **Dark Theme**: Sfondo scuro, testo chiaro
- 🎯 **Focus Colors**: Bordo blu su hover
- ⚪ **Default**: Tema scuro per ridurre affaticamento oculare

---

## 📊 Dati Visualizzati

### Per ogni giocatore vedi:
```
#01 - Mario Rossi (Palleggiatore)
└── Numero, Nome, Cognome, Ruolo
```

### Per ogni squadra vedi:
```
Nome | Abbreviazione | Categoria | Impianto | Logo
```

---

## 🔗 Associazioni Database

Quando salvi:
- **Squadra** → Creata/Modificata nella tabella `teams`
- **Giocatore** → Creato/Modificato nella tabella `players`
- **Foreign Key** → `players.team_id` = `teams.id`

Quando elimini:
- **Squadra** → Eliminata e tutti i suoi giocatori con essa (cascade)
- **Giocatore** → Eliminato singolarmente

---

## 📱 Responsive Design

La pagina si adatta automaticamente a:
- ✅ Monitor grandi (1920x1080+)
- ✅ Laptop standard (1366x768)
- ✅ Tablet (con alcune limitazioni)
- ❌ Mobile (non ottimizzato)

---

## ✅ Checklist di Verifica

Dopo ogni operazione, verifica:
- [ ] La lista si aggiorna automaticamente
- [ ] Nessun messaggio di errore nel terminale
- [ ] I dati sono persistenti (riavvia l'app per verificare)
- [ ] Le validazioni funzionano

---

## 🆘 Aiuto & Supporto

Se hai problemi:
1. Controlla il terminale per error messages
2. Verifica che il database sia accessibile
3. Assicurati che i campi obbligatori siano compilati
4. Ricarica l'app (F5 o riavvia)

---

**Versione**: 2.0
**Ultimo aggiornamento**: 2024
**Status**: ✅ Pronto all'uso
