# Match Management Widget - UI Design

## Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  MatchManagementWidget                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────── Crea Nuovo Match ──────────────────┐     │
│  │                                                  │     │
│  │  Squadra A (Home)  [Dropdown: Select team...]   │     │
│  │  Squadra B (Away)  [Dropdown: Select team...]   │     │
│  │  Data              [30/01/2025]                 │     │
│  │  Competizione      [Serie A1]                   │     │
│  │  Impianto          [Pala XYZ]                   │     │
│  │                                                  │     │
│  │  [Avvio Scout (Imposta Roster)]                 │     │
│  │                                                  │     │
│  └──────────────────────────────────────────────────┘     │
│                                                             │
│  ┌────────────── Match Salvati ──────────────────────┐    │
│  │                                                   │    │
│  │  ┌─────────────────────────────────────────────┐ │    │
│  │  │ ⏳ Team A vs Team B - 28/01/2025 10:30    │ │    │
│  │  │ (Yellow/Orange background, brown text)     │ │    │
│  │  └─────────────────────────────────────────────┘ │    │
│  │                                                   │    │
│  │  ┌─────────────────────────────────────────────┐ │    │
│  │  │ ✅ Team C vs Team D - 25/01/2025 18:00    │ │    │
│  │  │ (Green background, dark green text)        │ │    │
│  │  └─────────────────────────────────────────────┘ │    │
│  │                                                   │    │
│  │  ┌─────────────────────────────────────────────┐ │    │
│  │  │ ⏳ Team E vs Team F - 24/01/2025 14:15    │ │    │
│  │  │ (Yellow/Orange background, brown text)     │ │    │
│  │  └─────────────────────────────────────────────┘ │    │
│  │                                                   │    │
│  └───────────────────────────────────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Color Scheme Details

### "Da terminare" Status (draft / in_progress)
```
┌──────────────────────────────────────────────┐
│ ⏳ Team A vs Team B - 28/01/2025 10:30     │
├──────────────────────────────────────────────┤
│ Background: #FFF3CD (Giallo chiaro)          │
│ Border: Sottile grigio (#ddd)                │
│ Text Color: #856404 (Marrone scuro)          │
│ Icon: ⏳ (Hourglass emoji)                   │
│ Padding: 10px                                │
│ Border-radius: 3px                           │
└──────────────────────────────────────────────┘
```

### "Completato" Status (completed)
```
┌──────────────────────────────────────────────┐
│ ✅ Team C vs Team D - 25/01/2025 18:00      │
├──────────────────────────────────────────────┤
│ Background: #D4EDDA (Verde chiaro)           │
│ Border: Sottile grigio (#ddd)                │
│ Text Color: #155724 (Verde scuro)            │
│ Icon: ✅ (Checkmark emoji)                   │
│ Padding: 10px                                │
│ Border-radius: 3px                           │
└──────────────────────────────────────────────┘
```

## QListWidget Styling

```css
QListWidget {
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 5px;
}

QListWidget::item {
    padding: 10px;
    border-radius: 3px;
    margin: 2px 0px;
}

QListWidget::item:hover {
    /* Hover effect - PyQt default */
}

QListWidget::item:selected {
    /* Selected effect - PyQt default */
}
```

## Interactive Behaviors

### Click su Match "da terminare"

```
User clicks on "⏳ Team A vs Team B - 28/01/2025 10:30"
         ↓
Dialog appears:
┌──────────────────────────────────────┐
│        Continua Scout                │
├──────────────────────────────────────┤
│                                      │
│ Vuoi continuare lo scouting di       │
│ Team A vs Team B?                    │
│                                      │
│            [Yes]     [No]            │
└──────────────────────────────────────┘
         ↓ (if Yes)
resume_match.emit(match_id)
         ↓
show_formation_panel(match_id)
         ↓
Load formation setup for existing match
```

### Click su Match "completato"

```
User clicks on "✅ Team C vs Team D - 25/01/2025 18:00"
         ↓
Dialog appears:
┌──────────────────────────────────────┐
│      Match Completato                │
├──────────────────────────────────────┤
│                                      │
│ Match Team C vs Team D               │
│                                      │
│ Stato: Completato                    │
│ Data: 25/01/2025 18:00               │
│                                      │
│              [OK]                    │
└──────────────────────────────────────┘
         ↓
Dialog closes (read-only view)
```

## Responsive Design Notes

### Desktop (>1200px)
- QListWidget takes full width of the group box
- Each item height: ~40px
- Font size: 11pt (default)

### Tablet (800-1200px)
- Slight reduction in padding
- Same structure

### Mobile (not applicable)
- This is a desktop application

## Accessibility

- ✅ Clear color contrast (WCAG AA compliant)
  - Yellow text on white: contrast ratio ~10:1
  - Green text on white: contrast ratio ~6:1
- ✅ Icons + text (not icon-only)
- ✅ Large click target (40px minimum)
- ✅ Clear action labels

## Transition Animation (Future)

Consider adding smooth fade-in when items are loaded:
```python
# Future enhancement
animation = QPropertyAnimation(item, b"geometry")
animation.setDuration(300)
```

## Font Specifications

- **Family**: System default (QFont)
- **Size**: 11pt (default PyQt)
- **Weight**: Regular for item text
- **Group Box Title**: Bold (Qt automatically)

## Spacing

- **Outer padding** (group box): 5px
- **Item padding**: 10px
- **Item margin**: 2px (top/bottom)
- **Border width**: 1px
- **Border radius**: 5px (group) / 3px (items)

## Dark Mode Considerations

If dark mode is implemented in the future:
- "#FFF3CD" → "#665d1b" (dark yellow-brown)
- "#D4EDDA" → "#0f5132" (dark green)
- "#856404" → "#D3E4CD" (light brown)
- "#155724" → "#86EFAC" (light green)
- "#ddd" → "#444" (light gray borders)
