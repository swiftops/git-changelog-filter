from flask import Flask, request
from flask_cors import CORS
from change_log_util import fetch_required_entities, call_change_log, init
import logging


app = Flask(__name__)
CORS(app)
logging.basicConfig(filename='./log/app.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)
init(app)


@app.route("/change_log_filter", methods=['POST'])
def changelog_filter():
    try:
        request_values = request.json
        if request_values is None:
            required_entities = fetch_required_entities("change_log")
            if not bool(required_entities):
                data = call_change_log(None)
            else:
                data = {}
                logger.info("Mandatory entities required  : " + required_entities)
        else:
            data = call_change_log(request_values)
    except Exception as e:
        data = call_change_log(None)
    return data


if __name__ == "__main__":
    app.run('0.0.0.0', port=8084, debug=True)


