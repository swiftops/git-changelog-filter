from database_util import get_service_collection, get_master_collection
import pymongo, re
import requests, json
import logging
from flask import jsonify
from elasticapm.contrib.flask import ElasticAPM
from consul_util import get_config_value

logging.basicConfig(filename='./log/app.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _find_filter(keyword):
    """Fetches filter url for the given keyword (keyword can be change_log,performance)"""
    db = get_service_collection()
    result = db.find({"name": {"$regex": keyword}})
    service_endpoint = ''
    for item in result:
        service_endpoint = item["value"]["url"]
        break
    return service_endpoint


def _find_latest():
    """Returns latest release and its latest build"""
    try:
        db = get_master_collection()
        service_details = db.find({"master.key": "release"}).sort([("master.value", pymongo.DESCENDING)]).limit(1)
        for service in service_details:
            for r in sorted(service["master"]["value"], reverse=True):
                latest_release = r
                build_list = service["master"]["value"][r]
                break
            break

        latest_rel_num = str(latest_release).replace("_", ".")
        build_list = _natural_sort(build_list)
        for build in build_list:
            latest_build = build
            break

        latest_build_num = latest_build
        second_latest_build_num = int(latest_build_num) - 1
        latest = {"latest_val": latest_rel_num + "_" + latest_build_num,
                  "second_latest_val": latest_rel_num + "_" + str(second_latest_build_num)}
    except Exception as e:
        logger.error("Exception in _find_latest : " + str(e))
    return latest


def _call_rest_api(url, input_data):
    """invoke other microservices"""
    try:
        req = requests.get(url, params=input_data)
        response = req.text
        val = json.loads(response)
    except Exception as e:
        logger.error(str(e))
        raise ValueError("Change Log Microservice is down!!!!")
    return val


def call_change_log(input_filter):
    """If there is no details for changelog then get the latest release and its latest build
    and display the changelog of latest and its previous build else if details are provided
    then get the changelog between given and its previous build"""
    try:
        if input_filter is None:
            latest = _find_latest()
            service_endpoint = _find_filter("change_log")
        else:
            keyword = input_filter.split(" ")[0]
            if "release" == keyword or "build" == keyword:
                service_endpoint = _find_filter(input_filter.split(";")[2])
            else:
                service_endpoint = _find_filter(keyword)

            rel_build = input_filter.replace("_", ".").split(" ")[1].split(";")

            if "build" == keyword:
                latest_rel = rel_build[1]
                latest_bui = rel_build[0]
            else:
                latest_rel = rel_build[0]
                latest_bui = rel_build[1]

            latest = {"latest_val": latest_rel + "_" + latest_bui,
                      "second_latest_val": latest_rel + "_" + str(int(latest_bui)-1)}

        latest_query = latest["second_latest_val"] + ".." + latest["latest_val"]
        data = _call_rest_api(service_endpoint + "/" + latest_query, None)
    except Exception as e:
        logger.error(str(e))
        data = {"success": "", "data": {}, "error": {"Message": str(e)}}
        data = jsonify(data)
    return data


def _natural_sort(alphanumeric_data):
    """Alphanumeric sorting in reverse order to get latest release and build"""
    try:
        convert = lambda text: int(text) if text.isdigit() else text.lower()
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    except Exception as e:
        logger.error("Exception in _natural_sort : " + str(e))
    return sorted(alphanumeric_data, key=alphanum_key, reverse=True)


def fetch_required_entities(name):
    """Get required entities for the given service"""
    try:
        db = get_service_collection()
        service = db.find({"name": {"$regex": name.strip(), "$options": "i"}})
        required_entities = {}
        for change_log_service in service:
            entities = change_log_service["value"]["entities"]
            break

        for entity in entities:
            if "true" == entities[entity]["required"]:
                required_entities[entity] = entity
                break
    except Exception as e:
        logger.error("Exception in _fetch_required_entities : " + str(e))

    return required_entities


def init(app):
    apm = None
    if get_config_value('ENABLE_APM') is not None and 'Y' in str(get_config_value('ENABLE_APM')):
        app.config['ELASTIC_APM'] = {
            'SERVICE_NAME': 'changelogfilter',
            'SERVER_URL': get_config_value('APM_SERVER_URL').decode(encoding="utf-8"),
            'DEBUG': True
        }
        apm = ElasticAPM(app)
    return apm
