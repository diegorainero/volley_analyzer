# ⚡ Quick Start - Nuova Partita

## Come Creare una Nuova Partita

### Passo 1: Apri la Schermata Formation Setup
1. Avvia l'applicazione Volleyball Scout
2. Vai alla sezione **"🏐 Formation Setup"** dal menu principale

### Passo 2: Clicca su "➕ Nuova Partita"
Vedrai il pulsante sopra la lista delle partite

```
┌─────────────────────────────────────┐
│ 🏐 Selezione Partita per Formazione │
│ Clicca su una partita per...       │
│                                     │
│  [➕ Nuova Partita]  [🔄 Aggiorna]  │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Home | Away | Data | Status │   │
│  │ ─────────────────────────── │   │
│  │ ...                         │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Passo 3: Compila il Form

Si aprirà una finestra di dialogo:

```
┌──────────────────────────────────┐
│ ➕ Nuova Partita                 │
│                                  │
│ Crea una Nuova Partita           │
│                                  │
│ Squadra A (Home): [▼ Seleziona]  │
│ Squadra B (Away): [▼ Seleziona]  │
│ Data e Ora:       [31/12/2024]   │
│ Luogo:            [Testo libero] │
│ Note:             [Testo lungo]  │
│                                  │
│                [✅ Salva][❌ Annulla]
└──────────────────────────────────┘
```

**Campi da riempire:**

| Campo | Obbligatorio | Descrizione |
|-------|------|-------------|
| Squadra A (Home) | ✅ Sì | Scegli la squadra che gioca in casa |
| Squadra B (Away) | ✅ Sì | Scegli la squadra che gioca fuori |
| Data e Ora | ✅ Sì | Quando inizia la partita |
| Luogo | ❌ No | Dove si gioca (opzionale) |
| Note | ❌ No | Note aggiuntive sulla partita (opzionale) |

### Passo 4: Salva la Partita
Clicca il pulsante **"✅ Salva"**

Se tutto è corretto, vedrai un messaggio di conferma:
```
✅ Partita creata con successo!
```

### Passo 5: Selezione Automatica
La nuova partita sarà:
- Aggiunta alla lista (status: "🔲 Bozza")
- Selezionata automaticamente
- Pronta per inserire la formazione

---

## 🚨 Cosa Succede se Commetto un Errore?

### Errore: "Selezionare la Squadra A (Home)"
**Causa**: Non hai scelto una squadra per il campo "Home"  
**Soluzione**: Clicca sul dropdown e seleziona una squadra

### Errore: "La Squadra A e la Squadra B devono essere diverse"
**Causa**: Hai selezionato la stessa squadra in entrambi i campi  
**Soluzione**: Scegli due squadre diverse

### Errore: "Data/ora non valida"
**Causa**: La data inserita non è valida  
**Soluzione**: Usa il picker di data per selezionare una data corretta

### Errore: "Errore durante la creazione della partita"
**Causa**: Problema con il database  
**Soluzione**: Controlla la connessione e riprova

---

## 📝 Esempi

### Esempio 1: Partita Semplice
```
Squadra A (Home):  Modena Volley
Squadra B (Away):  Cuneo Volley
Data e Ora:        31/12/2024 18:00
Luogo:             (lasciato vuoto)
Note:              (lasciato vuoto)

Risultato: ✅ Partita creata come bozza
```

### Esempio 2: Partita Completa
```
Squadra A (Home):  Modena Volley
Squadra B (Away):  Cuneo Volley
Data e Ora:        31/12/2024 18:00
Luogo:             Palazzetto di Modena
Note:              Semifinale Coppa Italia

Risultato: ✅ Partita creata come bozza con tutti i dettagli
```

---

## 💡 Consigli Utili

1. **Data predefinita**: La data/ora di default è impostata a oggi. Cambiala se necessario.

2. **Team non in lista?**: Se non vedi il team che cerchi:
   - Vai prima a "Team Management" e crea il team
   - Poi torna a creare la partita

3. **Modificare dopo**: Puoi modificare i dati della partita selezionandola e aprendo la formazione

4. **Status della partita**: Le nuove partite iniziano sempre come "🔲 Bozza"
   - Diventano "⏳ In Corso" quando inizi lo scouting
   - Diventano "✅ Completato" alla fine

---

## 🔄 Flusso Tipico di Utilizzo

```
1. Clicca "➕ Nuova Partita"
   ↓
2. Scegli le squadre (obbligatorio)
   ↓
3. Imposta data/ora (obbligatorio)
   ↓
4. Aggiungi luogo/note (opzionale)
   ↓
5. Clicca "✅ Salva"
   ↓
6. La partita appare nella lista
   ↓
7. Clicca su di essa per inserire la formazione
   ↓
8. Inizia lo scouting!
```

---

## ❓ FAQ

**D: Posso creare partite retroattive (nel passato)?**  
R: Sì, il form accetta qualsiasi data valida, incluse date passate.

**D: Cosa succede se creo una partita e poi la elimino?**  
R: Attualmente non c'è una funzione di eliminazione diretta. Puoi cambiare lo stato a "Completato" per archiviarla.

**D: Quante partite posso creare?**  
R: Nessun limite. Il sistema gestisce centinaia di partite senza problemi.

**D: Posso duplicare una partita?**  
R: Attualmente no, ma è previsto per versioni future.

**D: I dati della partita vengono salvati subito?**  
R: Sì, quando clicchi "Salva" la partita viene scritta nel database immediatamente.

---

## 🎓 Prossimi Passi

Una volta creata una partita, puoi:

1. **Inserire la Formazione**: Clicca sulla partita per aprire l'editor di formazione
2. **Aggiungi Giocatori**: Seleziona i giocatori che giocheranno
3. **Inizia lo Scouting**: Registra gli eventi della partita
4. **Visualizza Statistiche**: Vedi le analitiche al termine

---

**Versione**: 1.0  
**Data**: 2024  
**Status**: ✅ Pronto all'uso
