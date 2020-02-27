release: python update_product.py & 
release: python app.py db init
release: python app.py db migrate
release: python app.py db upgrade
web: gunicorn app:app
