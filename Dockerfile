# Použijeme Python 3.9 na Debian Buster
FROM python:3.9-buster

# Aktualizace a instalace wkhtmltopdf
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pokračujte s vaším původním Dockerfile
# Nastavení pracovního adresáře
WORKDIR /app

# Zkopírování requirements.txt a instalace Python závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Zkopírování zbytku aplikace
COPY . .

# Spustíme váš Python skript při startu kontejneru
CMD ["python", "main.py"]