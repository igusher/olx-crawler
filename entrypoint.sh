pg_host=`cat /etc/hosts | grep pg | awk '{print $1}'`
export PG_HOST="$pg_host"
/opt/main.py
