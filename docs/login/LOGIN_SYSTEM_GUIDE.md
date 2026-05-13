# 🔐 Volleyball Scout - Login System Guide

## 📋 Overview

Il sistema di login è stato integrato in `app_dark.py` con le seguenti caratteristiche:

- ✅ **Auto-login all'avvio** con credenziali hardcoded
- ✅ **LoginDialog** per login manuale (fallback se auto-login fallisce)
- ✅ **Logout nel menu File** con conferma
- ✅ **Gestione stato autenticazione** traccia l'utente corrente
- ✅ **Tema scuro integrato** nel dialog di login
- ✅ **Shortcuts da tastiera** per velocità

---

## 🚀 Come Funziona

### 1️⃣ Avvio dell'Applicazione

```
VolleyballScoutApp.__init__()
  ↓
Initialize Database
  ↓
Setup sezioni UI (Dashboard, Teams, Formation, etc.)
  ↓
_create_menu_bar() (incluso Logout)
  ↓
_perform_auto_login() ← NUOVO
  ↓
Auto-login con credenziali hardcoded
  ↓
Se successo: Mostra Dashboard immediatamente
Se fallisce: Mostra LoginDialog
```

### 2️⃣ Auto-Login (Nuovo)

**Username:** `admin`  
**Password:** `password`

```python
def _perform_auto_login(self):
    """Esegui auto-login all'avvio"""
    print("🔐 Auto-login in corso...")
    
    username = "admin"
    password = "password"
    
    if self._verify_credentials(username, password):
        self.is_authenticated = True
        self.current_user = username
        self._show_section("dashboard")  # ✅ Dashboard subito
    else:
        self._show_login_dialog()  # Fallback a LoginDialog
```

### 3️⃣ LoginDialog (Popup se Auto-Login Fallisce)

Una finestra popup elegante con:
- Input Username (pre-compilato: "admin")
- Input Password (pre-compilato: "password")
- Bottone "✓ Accedi"
- Bottone "✗ Annulla"
- Tema scuro integrato

**Credenziali valide:**
| Username | Password |
|----------|----------|
| admin | password |
| coach | coach123 |
| scout | scout123 |

### 4️⃣ Logout (Menu File)

**Shortcut:** `Ctrl+L`

- Mostra dialog di conferma
- Se sì: torna al LoginDialog
- Se no: rimane nella dashboard
- Traccia lo stato di autenticazione

---

## 🎨 Componenti Aggiunti

### LoginDialog Class

```python
class LoginDialog(QDialog):
    """Dialog semplice per il login"""
    
    def __init__(self, parent=None):
        # Crea UI con tema scuro
        # Pre-compila credenziali di test
    
    def get_credentials(self) -> tuple:
        """Ritorna (username, password)"""
```

### Metodi Aggiunti a VolleyballScoutApp

| Metodo | Descrizione |
|--------|-------------|
| `_perform_auto_login()` | Auto-login all'avvio |
| `_show_login_dialog()` | Mostra popup di login |
| `_verify_credentials(username, password)` | Verifica le credenziali |
| `_perform_logout()` | Logout e torna al login |
| `showErrorDialog(title, message)` | Mostra dialogo di errore |

### Attributi Aggiunti a VolleyballScoutApp

| Attributo | Tipo | Descrizione |
|-----------|------|-------------|
| `is_authenticated` | bool | Se l'utente è loggato |
| `current_user` | str\|None | Nome utente corrente |

---

## 🎯 Stato Iniziale

All'avvio dell'applicazione:

```
1. Database viene connesso
2. Tutte le sezioni UI vengono caricate
3. Menu bar viene creato (con opzione Logout)
4. Auto-login viene eseguito automaticamente
5. Credenziali verificate: admin/password
6. Se ok: Dashboard viene mostrata immediatamente
7. Utente vede la dashboard senza interazione
8. Se login fallisce: LoginDialog viene mostrato
```

---

## 🔄 Flusso di Autenticazione

### Scenario 1: Auto-Login Successo (Caso Normale)

```
App Start
  ↓
[Auto-login con admin/password]
  ↓
✅ Credenziali valide
  ↓
is_authenticated = True
current_user = "admin"
  ↓
📊 Dashboard mostrata
```

### Scenario 2: Auto-Login Fallisce

```
App Start
  ↓
[Auto-login fallisce]
  ↓
❌ Credenziali non valide
  ↓
[LoginDialog mostrato]
  ↓
Utente inserisce credenziali
  ↓
Se corrette: Accedi + Dashboard
Se sbagliate: "Credenziali non valide, riprova"
```

### Scenario 3: Logout

```
Menu File → Logout
  ↓
[Mostra conferma]
  ↓
is_authenticated = False
current_user = None
  ↓
[LoginDialog mostrato]
  ↓
Utente deve re-autenticarsi
```

---

## 🛠️ Integrazione con Database (Futuro)

Attualmente le credenziali sono hardcoded. Per integrazione reale:

```python
def _verify_credentials(self, username: str, password: str) -> bool:
    """Verifica le credenziali nel database"""
    try:
        user = self.db.get_user_by_username(username)
        if user and user.verify_password(password):
            return True
    except Exception as e:
        print(f"❌ Errore verifica credenziali: {e}")
    return False
```

---

## 🎬 Menu Bar Aggiornato

**File Menu:**
- 🚪 **Logout** (Ctrl+L) ← NUOVO
- ───────────── (separator)
- ❌ Esci (Ctrl+Q)

**Visualizza Menu:**
- 📊 Dashboard
- 👥 Teams & Players
- 📋 Roster Setup
- 🏐 Formation Setup
- 🎥 Scout & Video
- 📈 Statistics

**Aiuto Menu:**
- ℹ️ About (mostra anche l'utente corrente)

---

## 📱 Tema Scuro per LoginDialog

Aggiunto stile CSS per:
- `QLineEdit`: Sfondo scuro, bordi blu all'hover
- `QDialog`: Sfondo scuro #1e1e1e, testo chiaro
- Coerente con il resto dell'applicazione

---

## 💡 Note di Implementazione

### Pre-compilazione Credenziali

I campi username e password sono pre-compilati con le credenziali di test per facilità di prototipazione:

```python
self.username_input.setText("admin")
self.password_input.setText("password")
```

**Per produzione:** Rimuovere queste linee per una UI più sicura.

### Shortcut Return Key

Premendo Enter nel campo password si invia il form automaticamente:

```python
self.password_input.returnPressed.connect(self.accept)
```

### Error Handling

- Se il database non si connette: Messaggio di errore e chiusura
- Se auto-login fallisce: Fallback al LoginDialog
- Se login manuale fallisce: Messaggio "Credenziali non valide, riprova"
- Se utente annulla login: Applicazione si chiude

---

## 🧪 Testing

Per testare il sistema:

### Test 1: Auto-Login Successo
```bash
$ python volley_analizer/volleyball_scout/ui/app_dark.py
# Attendi 1 secondo
# Vedi: "🔐 Auto-login in corso..."
# Poi: "✅ Auto-login riuscito per utente: admin"
# Dashboard viene mostrata
```

### Test 2: Logout e Re-Login
```
1. Menu File → Logout
2. Conferma logout
3. LoginDialog appare
4. Inserisci credenziali (o premi Invio con i default)
5. Dashboard riappare
```

### Test 3: Credenziali Sbagliate
```
1. Menu File → Logout
2. Conferma logout
3. LoginDialog appare
4. Cambia password (es. "wrong")
5. Premi Accedi
6. Messaggio: "❌ Credenziali non valide. Riprova."
7. LoginDialog rimane aperto
```

---

## 📊 Credenziali di Test

| Utente | Password | Ruolo |
|--------|----------|-------|
| **admin** | **password** | Amministratore (default) |
| coach | coach123 | Coach |
| scout | scout123 | Scout |

---

## 🔒 Sicurezza

**Nota:** Questo è un prototipo con credenziali hardcoded. Per produzione:

1. ✅ Integrare con database reale
2. ✅ Usare hashing delle password (bcrypt/argon2)
3. ✅ Aggiungere rate limiting su login falliti
4. ✅ Implementare session tokens
5. ✅ Aggiungere 2FA (opzionale)
6. ✅ Logging degli accessi

---

## 📝 Modifica File

**File modificato:** `volley_analizer/volleyball_scout/ui/app_dark.py`

**Sezioni modificate:**
- ✅ Aggiunti import: `QDialog`, `QLineEdit`, `QMessageBox`
- ✅ Aggiunto stile CSS per `QLineEdit` e `QDialog`
- ✅ Creata nuova classe `LoginDialog`
- ✅ Aggiunto attributi di stato: `is_authenticated`, `current_user`
- ✅ Riordinato `__init__`: Menu bar creato prima dell'auto-login
- ✅ Aggiunto logout nel menu File
- ✅ Implementati metodi di autenticazione
- ✅ Rimosso `db.close()` (metodo non disponibile)

---

## 🎯 Prossimi Step (Opzionali)

1. **Database Integration:** Salvare utenti nel database
2. **Session Management:** Tracciare sessioni utente
3. **Audit Logging:** Registrare login/logout
4. **Role-Based Access:** Limitare funzionalità per ruolo
5. **Password Reset:** Aggiungere recovery password
6. **Two-Factor Auth:** Autenticazione a due fattori

---

## ✅ Checklist

- [x] LoginDialog creato
- [x] Auto-login implementato
- [x] Logout nel menu File
- [x] Credenziali verificate
- [x] Tema scuro per dialog
- [x] Shortcuts da tastiera
- [x] Error handling
- [x] Stato autenticazione tracciato
- [x] About mostra utente corrente

**Status:** ✅ **IMPLEMENTAZIONE COMPLETA**
