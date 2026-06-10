from flask import Flask
import random
import time
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route("/")
def index():
    delay = random.uniform(0.05, 0.5)
    time.sleep(delay)

    if random.random() < 0.1:
        logging.error("simulated error on GET /")
        return "simulated error", 500

    logging.info("successful GET /")
    return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)