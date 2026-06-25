! set -a && . /etc/dcfsite.env && set +a && .venv/bin/python manage.py collectstatic --noinput && systemctl restart dcfsite.service && systemctl is-active dcfsite.service
