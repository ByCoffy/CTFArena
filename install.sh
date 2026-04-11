#!/bin/bash
# =============================================================
# HackArena CTF Platform - Script de instalación para Ubuntu
# =============================================================
# Uso: sudo bash install.sh
# =============================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║       HackArena CTF Platform              ║"
echo "  ║       Instalación en Ubuntu Server         ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[!] Ejecuta este script como root: sudo bash install.sh${NC}"
    exit 1
fi

# Config
DB_NAME="ctf_platform"
DB_USER="ctf_user"
DB_PASS="ctf_password_$(openssl rand -hex 8)"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ADMIN_PASS="Admin_$(openssl rand -hex 6)!"
APP_DIR="/opt/hackarena-ctf"

echo -e "${YELLOW}[*] Actualizando sistema...${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}[*] Instalando dependencias...${NC}"
apt install -y python3 python3-pip python3-venv mariadb-server mariadb-client \
    nginx git

echo -e "${YELLOW}[*] Configurando MariaDB...${NC}"
systemctl start mariadb
systemctl enable mariadb

# Create database and user
mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';"
mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"
echo -e "${GREEN}[+] Base de datos '${DB_NAME}' creada.${NC}"

echo -e "${YELLOW}[*] Configurando aplicación...${NC}"
# Copy app files
mkdir -p ${APP_DIR}
cp -r . ${APP_DIR}/
cd ${APP_DIR}

# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file
cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
DATABASE_URL=mysql+pymysql://${DB_USER}:${DB_PASS}@localhost/${DB_NAME}
CTF_NAME=HackArena CTF
CTF_DESCRIPTION=Plataforma de Capture The Flag - Hacking Ético
FIRST_BLOOD_BONUS=50
MAX_TEAM_SIZE=5
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@hackarena.local
ADMIN_PASSWORD=${ADMIN_PASS}
EOF

# Create envloader for config
cat > env_loader.py << 'PYEOF'
import os
from dotenv import load_dotenv
load_dotenv()
PYEOF

pip install python-dotenv

# Update config.py to load .env
sed -i '1s/^/from dotenv import load_dotenv\nload_dotenv()\n\n/' config.py

# Initialize database
python setup_db.py

# Create uploads directory
mkdir -p app/static/uploads
chown -R www-data:www-data ${APP_DIR}

echo -e "${YELLOW}[*] Configurando Gunicorn como servicio...${NC}"
cat > /etc/systemd/system/hackarena-ctf.service << EOF
[Unit]
Description=HackArena CTF Platform
After=network.target mariadb.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable hackarena-ctf
systemctl start hackarena-ctf

echo -e "${YELLOW}[*] Configurando Nginx...${NC}"
cat > /etc/nginx/sites-available/hackarena-ctf << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/hackarena-ctf/app/static;
        expires 1d;
    }
}
EOF

ln -sf /etc/nginx/sites-available/hackarena-ctf /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ ¡HackArena CTF instalado correctamente!              ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  URL:    http://$(hostname -I | awk '{print $1}')                          ║${NC}"
echo -e "${GREEN}║  Admin:  admin / ${ADMIN_PASS}          ║${NC}"
echo -e "${GREEN}║  DB:     ${DB_USER} / ${DB_PASS}  ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Comandos útiles:                                        ║${NC}"
echo -e "${GREEN}║  - Estado:    systemctl status hackarena-ctf             ║${NC}"
echo -e "${GREEN}║  - Logs:      journalctl -u hackarena-ctf -f             ║${NC}"
echo -e "${GREEN}║  - Reiniciar: systemctl restart hackarena-ctf            ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}[!] GUARDA estas credenciales en un lugar seguro.${NC}"
