from flask_restful import Api
from blueprints import app, manager
from logging.handlers import RotatingFileHandler
from werkzeug.contrib.cache import SimpleCache
import logging, sys


cache = SimpleCache()
api = Api(app, catch_all_404s=True)


if __name__ == "__main__":
    try:
        if sys.argv[1] == "db":
            manager.run()
    except Exception as error:
        log_path = "../storage/logs"
        logging.basicConfig(level=logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s"
        )
        log_handler = RotatingFileHandler(
            "%s/%s" %(app.root_path, log_path+"/app.log"), maxBytes=1000000, backupCount=10
        )
        log_handler.setFormatter(formatter)
        app.logger.addHandler(log_handler)
        app.run(debug=True, host="localhost", port="5000")
