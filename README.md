# Rücklagenplaner

Mit dem **Rücklagenplaner** behältst du deine Verträge, Abos und jährlichen Ausgaben immer im Blick!
Die App berechnet, wie viel Geld du monatlich für jede wiederkehrende Zahlung zurücklegen solltest, und zeigt dir jederzeit, wie viel auf deinem Tagesgeldkonto liegen muss.

---

## Features

* **Verträge mit beliebigen Zyklen:** jährlich, halbjährlich, vierteljährlich, benutzerdefiniert (z.B. alle 24 Monate)
* **Automatische Sparraten-Berechnung** für jeden Vertrag
* **Filter & Sortiermöglichkeiten** (Kategorien, Konten)
* **Grafische Darstellung** des Kontoverlaufs (Plotly)
* **Übersicht & Verlauf in Tabs**
* **Einfache Bearbeitung, Löschen, Hinzufügen von Einträgen**
* **Datenspeicherung als JSON-Datei** im Projektordner (`data/entries.json`)
* **Mobil und Desktop nutzbar**

---

## Voraussetzungen

* **Python 3.8 oder neuer**
* **pip** (Python-Paketmanager)
* **(optional, empfohlen)** Eigene Domain und Linux-Server mit Nginx für produktiven Betrieb

---

## Installation

### 1. Repo klonen

```bash
git clone https://github.com/sgtsilvergreen/ruecklagenplaner.git
cd ruecklagenplaner
```

### 2. Abhängigkeiten installieren

#### a) Lokal (empfohlen mit virtualenv)

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### b) Systemweit (nur falls nötig)

```bash
pip install --break-system-packages -r requirements.txt
```

### 3. Datenverzeichnis anlegen

```bash
mkdir -p data
echo "[]" > data/entries.json
```

> **Tipp:**
> Die Datei `data/entries.json` wird beim ersten Start automatisch angelegt, falls sie fehlt.
> Du kannst sie auch manuell anpassen/mit Daten befüllen.

---

## Starten der App

```bash
streamlit run Ruecklagenplaner.py
```

**Die App ist dann unter** [http://localhost:8501](http://localhost:8501) **erreichbar.**

---

## Produktivbetrieb mit eigenem Server (Linux + Nginx + Domain + SSL)

### 1. Systemd-Service (optional)

Erstelle `/etc/systemd/system/streamlit.service`:

```ini
[Unit]
Description=Streamlit App Ruecklagenplaner
After=network.target

[Service]
WorkingDirectory=/pfad/zum/projektordner
ExecStart=/usr/local/bin/streamlit run Ruecklagenplaner.py --server.address localhost
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

Aktivieren & starten:

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
```

### 2. Nginx-Proxy mit WebSocket-Support

Nginx-Konfiguration (Beispiel):

```nginx
server {
    listen 80;
    server_name deine-domain.de;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name deine-domain.de;

    ssl_certificate /etc/letsencrypt/live/deine-domain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/deine-domain.de/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://localhost:8501/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
```

> **Vergiss nicht, nach jeder Änderung:**
>
> ```bash
> sudo nginx -t && sudo systemctl reload nginx
> ```

---

## **Nutzung & Tipps**

* **Daten werden in `data/entries.json` gespeichert.**

  * Diese Datei kannst du sichern, verschieben oder versionieren.
* **App läuft nach Änderungen/Updates einfach per:**

  ```bash
  git pull
  sudo systemctl restart streamlit
  ```
* **Statistik-Tracking deaktivieren:**
  Erstelle die Datei `~/.streamlit/config.toml` und füge ein:

  ```toml
  [browser]
  gatherUsageStats = false
  ```

---

## **Fehlerbehebung**

* **App zeigt nur „Streamlit“ im Tab und pulsiert:**

  * WebSockets sind im Nginx-Proxy nicht korrekt konfiguriert!
    → Siehe Nginx-Beispiel oben.
* **entries.json fehlt/ist kaputt:**

  * Einfach leere Liste einfügen: `[]`
* **„externally-managed-environment“-Fehler:**

  * Mit `pip install --break-system-packages ...` installieren
