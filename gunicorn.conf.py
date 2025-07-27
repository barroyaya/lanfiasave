# gunicorn.conf.py - Configuration optimisée pour Render
# PLACEZ CE FICHIER À LA RACINE DU PROJET (même niveau que manage.py)

import os

# Configuration des workers
workers = 1  # Un seul worker pour économiser la mémoire
worker_class = "sync"
worker_connections = 1000

# Timeouts augmentés
timeout = 120  # 2 minutes au lieu de 30 secondes
keepalive = 5
max_requests = 1000
max_requests_jitter = 100

# Gestion mémoire
preload_app = True  # Charge l'app une fois pour tous les workers
worker_tmp_dir = "/dev/shm"  # Utilise la mémoire partagée

# Configuration réseau
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Limites mémoire
worker_memory_limit = 300 * 1024 * 1024  # 300MB par worker