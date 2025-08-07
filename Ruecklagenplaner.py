import streamlit as st
import json
import uuid
import os
import pandas as pd
import plotly.express as px
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "entries.json")
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

deutsche_monate = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]

TURNUS_MAPPING = {
    "Vierteljährlich": 3,
    "Halbjährlich": 6,
    "Jährlich": 12,
    "Benutzerdefiniert": None,
}

def load_entries():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_entries(entries):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(entries, f, indent=2)

def add_entry(entry):
    entries = load_entries()
    entries.append(entry)
    save_entries(entries)

def delete_entry(entry_id):
    entries = load_entries()
    entries = [e for e in entries if e.get("id") != entry_id]
    save_entries(entries)

def update_entry(entry_id, new_data):
    entries = load_entries()
    for i, e in enumerate(entries):
        if e.get("id") == entry_id:
            entries[i] = new_data
            break
    save_entries(entries)
    
def calculate_monthly_saving_and_progress(entry):
    today = datetime.now().replace(day=1)
    contract_start = datetime.strptime(entry["start_date"], "%Y-%m")
    due_month = int(entry["due_month"])
    cycle = entry["custom_cycle"] if entry["cycle"] == "Benutzerdefiniert" else TURNUS_MAPPING[entry["cycle"]]
    amount = entry["amount"]

    # Erste Fälligkeit nach Vertragsbeginn
    first_due = datetime(year=contract_start.year, month=due_month, day=1)
    if first_due < contract_start:
        first_due = datetime(year=contract_start.year + 1, month=due_month, day=1)

    # Vertrag noch nicht aktiv
    if today < contract_start:
        return 0, 0, contract_start.strftime("%m.%Y")

    # Sonderfall: Start = Fälligkeitsmonat
    if contract_start.year == first_due.year and contract_start.month == first_due.month:
        months_total = cycle
        cycle_start = contract_start
        next_due = first_due
    else:
        months_total = (first_due.year - contract_start.year) * 12 + (first_due.month - contract_start.month)
        cycle_start = contract_start
        next_due = first_due

    # Nach erstem Zyklus → Zyklusstart und nächste Fälligkeit anpassen
    while today >= next_due:
        cycle_start = next_due
        next_due = next_due + pd.DateOffset(months=cycle)
        months_total = cycle

    # Berechne wie viele Monate seit Zyklusstart vergangen sind (Sparmonate)
    # Gespart wird **bis einschließlich Monat vor nächster Fälligkeit**
    if today < next_due:
        months_saved = (today.year - cycle_start.year) * 12 + (today.month - cycle_start.month) + 1
        # Aber: im Fälligkeitsmonat selbst wird keine Rate für diesen Zyklus mehr gespart!
        if today.year == next_due.year and today.month == next_due.month:
            months_saved -= 1
    else:
        months_saved = months_total

    months_saved = max(0, min(months_saved, months_total))
    rate = amount / months_total if months_total > 0 else 0
    saved = rate * months_saved
    percent = saved / amount if amount > 0 else 0
    return rate, percent, saved, None if today >= contract_start else contract_start.strftime("%m.%Y")


# Neue Berechnung: due_month statt due_date!
def calculate_saldo_over_time(entries, months_before=36, months_after=36):
    if not entries:
        return pd.DataFrame(columns=["month", "saldo"])
    # Setze das echte früheste Vertragsstartdatum als Start!
    earliest_start = min([datetime.strptime(e['start_date'], "%Y-%m") for e in entries])
    today = datetime.now().replace(day=1)
    # Nur noch Start bei earliest_start oder heute, je nachdem was „früher“ ist:
    start_date = min(today, earliest_start)
    end_date = today + pd.DateOffset(months=months_after)
    months = pd.date_range(start=start_date, end=end_date, freq='MS')

    saldo = {}
    account = 0.0
    zyklusstand = {}

    for entry in entries:
        cycle_months = entry["custom_cycle"] if entry["cycle"] == "Benutzerdefiniert" else TURNUS_MAPPING[entry["cycle"]]
        contract_start = datetime.strptime(entry["start_date"], "%Y-%m")
        end = datetime.strptime(entry["end_date"], "%Y-%m") if entry.get("end_date") else months[-1]
        name = entry["name"]
        due_month = int(entry["due_month"])
        amount = entry["amount"]

        # Normales erstes Fälligkeitsdatum:
        first_due = datetime(year=contract_start.year, month=due_month, day=1)
        if first_due < contract_start:
            first_due = datetime(year=contract_start.year + 1, month=due_month, day=1)

        # *** Sonderfall: Startmonat = Fälligkeitsmonat ***
        if contract_start.year == first_due.year and contract_start.month == first_due.month:
            # Abbuchung erst nach vollem Turnus
            first_due = first_due + pd.DateOffset(months=cycle_months)
            months_left = cycle_months
        else:
            # Spare bis Monat vor erster Fälligkeit
            months_left = (first_due.year - contract_start.year) * 12 + (first_due.month - contract_start.month)

        zyklusstand[name] = {
            "next_due": first_due,
            "rate": amount / months_left if months_left > 0 else amount,
            "first_cycle": True
    }

    for month in months:
        key = month.strftime("%Y-%m")
        monthly_plus = 0.0
        monthly_minus = 0.0

        for entry in entries:
            cycle_months = entry["custom_cycle"] if entry["cycle"] == "Benutzerdefiniert" else TURNUS_MAPPING[entry["cycle"]]
            contract_start = datetime.strptime(entry["start_date"], "%Y-%m")
            end = datetime.strptime(entry["end_date"], "%Y-%m") if entry.get("end_date") else months[-1]
            name = entry["name"]
            amount = entry["amount"]
            due_month = int(entry["due_month"])
            next_due = zyklusstand[name]["next_due"]
            rate = zyklusstand[name]["rate"]
            first_cycle = zyklusstand[name]["first_cycle"]

            if month < contract_start or month > end:
                continue

            if first_cycle:
                if month < next_due:
                    monthly_plus += rate
                elif month.year == next_due.year and month.month == next_due.month:
                    monthly_minus += amount
                    # Jetzt ab diesem Monat: neue Rate (ab sofort!)
                    zyklusstand[name]["next_due"] = next_due + pd.DateOffset(months=cycle_months)
                    zyklusstand[name]["rate"] = amount / cycle_months if cycle_months > 0 else amount
                    zyklusstand[name]["first_cycle"] = False
                    monthly_plus += zyklusstand[name]["rate"]  # <-- neue Rate sofort im Fälligkeitsmonat!
            else:
                if month.year == next_due.year and month.month == next_due.month:
                    monthly_minus += amount
                    zyklusstand[name]["next_due"] = next_due + pd.DateOffset(months=cycle_months)
                    zyklusstand[name]["rate"] = amount / cycle_months if cycle_months > 0 else amount
                    monthly_plus += zyklusstand[name]["rate"]  # <-- neue Rate sofort im Fälligkeitsmonat!
                elif month > contract_start and month < next_due:
                    monthly_plus += rate

        account += monthly_plus
        account -= monthly_minus
        saldo[key] = account

    df_saldo = pd.DataFrame([{"month": k, "saldo": v} for k, v in saldo.items()])
    return df_saldo

entries = load_entries()

st.set_page_config(page_title="Rücklagenplaner", layout="wide")
st.title("📊 Rücklagen für Einmalausgaben planen")


# =======================
# === Sidebar Abschnitt
# =======================

st.sidebar.header("➕ Neuen Eintrag hinzufügen")
name = st.sidebar.text_input("Bezeichnung", key="add_name")
amount = st.sidebar.number_input("Betrag (€)", min_value=0.01, key="add_amount")
konto = st.sidebar.text_input("Konto", key="add_konto")
category = st.sidebar.text_input("Kategorie", key="add_category")
cycle = st.sidebar.selectbox("Turnus", list(TURNUS_MAPPING.keys()), key="add_cycle")
custom_cycle = None
if cycle == "Benutzerdefiniert":
    custom_cycle = st.sidebar.number_input("Benutzerdefinierter Turnus (Monate)", min_value=1, value=12, key="add_custom_cycle")
due_month = st.sidebar.selectbox("Fälligkeitsmonat", list(range(1, 13)), format_func=lambda x: f"{x:02d}", key="add_due_month")
start_month = st.sidebar.selectbox("Startmonat", list(range(1, 13)), format_func=lambda x: f"{x:02d}", key="add_start_month")
start_year = st.sidebar.number_input("Startjahr", min_value=2020, max_value=2100, value=datetime.today().year, key="add_start_year")
start_date = f"{start_year}-{start_month:02d}"
use_end_date = st.sidebar.checkbox("Enddatum setzen?", key="add_use_end_date")
if use_end_date:
    end_month = st.sidebar.selectbox("Endmonat", list(range(1, 13)), format_func=lambda x: f"{x:02d}", key="add_end_month")
    end_year = st.sidebar.number_input("Endjahr", min_value=2020, max_value=2100, value=datetime.today().year, key="add_end_year")
    end_date = f"{end_year}-{end_month:02d}"
else:
    end_date = None

if st.sidebar.button("Hinzufügen", key="add_submit"):
    entry = {
        "id": str(uuid.uuid4()),
        "name": name,
        "amount": amount,
        "konto": konto,
        "category": category,
        "cycle": cycle,
        "custom_cycle": int(custom_cycle) if cycle == "Benutzerdefiniert" else None,
        "due_month": due_month,
        "start_date": start_date,
        "end_date": end_date
    }
    add_entry(entry)
    st.sidebar.success("Eintrag gespeichert.")
    st.rerun()
    
# =======================
# === Sidebar Ende
# =======================

tab1, tab2 = st.tabs(["Übersicht", "Kontoverlauf"])

with tab1:
    st.subheader("🗂 Übersicht der Rücklagen")    
    # =======================
    # === Filter Abschnitt
    # ======================= 
    all_categories = sorted(set(e.get("category", "") for e in entries if e.get("category", "")))
    all_konten = sorted(set(e.get("konto", "") for e in entries if e.get("konto", "")))
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        selected_category = st.selectbox("Kategorie",["Alle"] + all_categories,key="filter_category_tab1")
    with col2:
        selected_konto = st.selectbox("Konto",["Alle"] + all_konten,key="filter_konto_tab1")
    with col3:
        sort_option = st.selectbox("Sortierung",["Name", "Fälligkeitsmonat", "Monatlicher Beitrag"],key="sort_option_tab1")
        filtered_entries = [
            e for e in entries
            if (selected_category == "Alle" or e.get("category", "") == selected_category)
            and (selected_konto == "Alle" or e.get("konto", "") == selected_konto)
        ]
    with col4:
                # Hier könntest du später noch einen Zeitraumfilter ergänzen!
        pass
    if sort_option == "Fälligkeitsmonat":
        filtered_entries.sort(key=lambda x: x["due_month"])
    elif sort_option == "Monatlicher Beitrag":
        filtered_entries.sort(key=lambda x: calculate_monthly_saving_and_progress(x), reverse=True)
    else:
        filtered_entries.sort(key=lambda x: x["name"].lower())
    # =======================
    # === Filter Ende
    # ======================= 
    st.markdown("---")
    # =======================
    # === Übersicht Abschnitt
    # ======================= 
    # Nach deinem Filter/Suchbereich und vor den Einträgen
    for e in filtered_entries:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1.5])
        with col1:
            st.markdown(f"**{e['name']}**\n({e.get('category', 'Unkategorisiert')})")
        with col2:
            monat_name = deutsche_monate[int(e['due_month'])]
            st.markdown(f"Fälligkeitsmonat: {monat_name}")
        with col3:
            rate, percent, saved, info = calculate_monthly_saving_and_progress(e)
            if info:
                st.markdown(f"Monatlich zurücklegen: **{rate:.2f} €** (ab {info})")
            else:
                st.markdown(f"Monatlich zurücklegen: **{rate:.2f} €**")
        with col4:
            rate, percent, saved, info = calculate_monthly_saving_and_progress(e)
            if info:
                st.progress(0, text="Noch nicht gestartet")
            else:
                st.progress(percent, text=f"{percent*100:.1f}% von {e['amount']:.2f} € gespart ({saved:.2f} €)")
        with col5:
            col_btn1, col_btn2 = st.columns([0.2, 1])
            with col_btn1:
                if st.button("✏️", key=f"edit_{e['id']}"):
                    st.session_state["edit_id"] = e["id"]
            with col_btn2:
                if st.button("❌", key=f"delete_{e['id']}"):
                    delete_entry(e["id"])
                    st.rerun()

        # Bearbeiten-Funktion, Sidebar, nur wenn edit_id gesetzt
        edit_id = st.session_state.get("edit_id")
        entry = next((e for e in entries if e["id"] == edit_id), None)
        if entry:
            st.sidebar.header("✏️ Eintrag bearbeiten")
            name = st.sidebar.text_input("Bezeichnung", value=entry["name"], key="edit_name")
            amount = st.sidebar.number_input("Betrag (€)", min_value=0.01, value=entry["amount"], key="edit_amount")
            konto = st.sidebar.text_input("Konto", key="edit_konto")
            category = st.sidebar.text_input("Kategorie", value=entry["category"], key="edit_category")
            cycle = st.sidebar.selectbox("Turnus", list(TURNUS_MAPPING.keys()),index=list(TURNUS_MAPPING.keys()).index(entry["cycle"]),key="edit_cycle")
            
            if cycle == "Benutzerdefiniert":
                custom_cycle = st.sidebar.number_input("Benutzerdefinierter Turnus (Monate)",min_value=1,value=entry.get("custom_cycle", 12),key="edit_custom_cycle")
            else:
                custom_cycle = None
                
            due_month = st.sidebar.selectbox("Fälligkeitsmonat", list(range(1, 13)),format_func=lambda x: f"{x:02d}",index=int(entry["due_month"]) - 1,key="edit_due_month")
            start_month = st.sidebar.selectbox("Startmonat", list(range(1, 13)),format_func=lambda x: f"{x:02d}",index=int(entry["start_date"].split("-")[1]) - 1,key="edit_start_month")
            start_year = st.sidebar.number_input("Startjahr", min_value=2020, max_value=2100,value=int(entry["start_date"].split("-")[0]),key="edit_start_year")
            start_date = f"{int(start_year)}-{int(start_month):02d}"
            use_end_date = st.sidebar.checkbox("Enddatum setzen?", value=bool(entry.get("end_date")), key="edit_use_end_date")
            
            if use_end_date:
                if entry.get("end_date"):
                    end_month_val = int(entry["end_date"].split("-")[1])
                    end_year_val = int(entry["end_date"].split("-")[0])
                else:
                    end_month_val = 1
                    end_year_val = int(start_year)
                    
                end_month = st.sidebar.selectbox("Endmonat", list(range(1, 13)),format_func=lambda x: f"{x:02d}",index=end_month_val - 1,key="edit_end_month")
                end_year = st.sidebar.number_input("Endjahr", min_value=2020, max_value=2100,value=end_year_val,key="edit_end_year")
                end_date = f"{int(end_year)}-{int(end_month):02d}"
                
            else:
                end_date = None

            if st.sidebar.button("Speichern", key="edit_submit"):
                new_data = {
                    "id": entry["id"],
                    "name": name,
                    "amount": amount,
                    "konto": konto,
                    "category": category,
                    "cycle": cycle,
                    "custom_cycle": int(custom_cycle) if cycle == "Benutzerdefiniert" else None,
                    "due_month": due_month,
                    "start_date": start_date,
                    "end_date": end_date
                }
                update_entry(entry["id"], new_data)
                del st.session_state["edit_id"]
                st.sidebar.success("Eintrag aktualisiert.")
                st.rerun()
        elif "edit_id" in st.session_state:
            # Edit-Eintrag nicht gefunden (z.B. gelöscht) → aufräumen!
            del st.session_state["edit_id"]    
    # =======================
    # === Übersicht Ende
    # ======================= 
with tab2:
    st.subheader("💰 Kontostand-Verlauf mit Abbuchungen")
    # =======================
    # === Filter Abschnitt
    # ======================= 
    all_categories_Tab2 = sorted(set(e.get("category", "") for e in entries if e.get("category", "")))
    all_konten_Tab2 = sorted(set(e.get("konto", "") for e in entries if e.get("konto", "")))
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        selected_category = st.selectbox("Kategorie",["Alle"] + all_categories_Tab2,key="filter_category_tab2")
    with col2:
        selected_konto = st.selectbox("Konto",["Alle"] + all_konten_Tab2,key="filter_konto_tab2")
    with col3:
        # Hier könntest du später noch einen Zeitraumfilter ergänzen!
        pass
    filtered_entries_tab2 = [
        e for e in entries
        if (selected_category == "Alle" or e.get("category", "") == selected_category)
        and (selected_konto == "Alle" or e.get("konto", "") == selected_konto)
    ]
    # =======================
    # === Filter Ende
    # ======================= 
    # --- Kategorie-Filter (Dropdown) ---

    df_saldo = calculate_saldo_over_time(filtered_entries_tab2)
    
    deutsche_monate = [
    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
    ]
    df_saldo["Monatsname"] = df_saldo["month"].apply(
    lambda x: f"{deutsche_monate[int(x.split('-')[1])]} {x.split('-')[0]}"
    )


    fig_saldo = px.line(
        df_saldo,
        x="month",
        y="saldo",
        markers=True,
        labels={"saldo": "Kontostand (€)"},
        title="Entwicklung des Rücklagen-Kontos über Zeit",
        hover_name="Monatsname",
        hover_data={
            "saldo": ":.2f",
            "month": False  # Verstecke Rohmonat
        },
    )

    fig_saldo.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Kontostand: <b>%{y:.2f} €</b><extra></extra>",
        customdata=df_saldo[["Monatsname"]].values,
    )

    fig_saldo.update_layout(
        autosize=True,
        height=600,
        margin=dict(l=40, r=40, t=80, b=40),
        yaxis=dict(autorange=True, fixedrange=False),
        xaxis=dict(autorange=True, fixedrange=False),
    )
    st.plotly_chart(fig_saldo, use_container_width=True, config={"scrollZoom": True})
