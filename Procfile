release: python update_product.py & 
release: python app.py db init
release: python app.py db migrate
release: python app.py db upgrade
release: mysql --user=$THIS_UNAME --password=$THIS_PWD -e "create database if not exists $THIS_DB_DEV; create database if not exists $THIS_DB_TEST"
web: gunicorn app:app
