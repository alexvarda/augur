from flask import Flask, jsonify, request, Response
import click, logging, requests, json
from metric_status_worker.worker import MetricStatusWorker
import os
import json

logging.basicConfig(filename='worker.log', filemode='w', level=logging.INFO)


def create_server(app, gw):
    """ Consists of AUGWOP endpoints for the broker to communicate to this worker
    Can post a new task to be added to the workers queue
    Can retrieve current status of the worker
    Can retrieve the workers config object
    """
    
    @app.route("/AUGWOP/task", methods=['POST', 'GET'])
    def augwop_task():
        """ AUGWOP endpoint that gets hit to add a task to the workers queue or is used to get the heartbeat/status of worker
        """
        if request.method == 'POST': #will post a task to be added to the queue
            logging.info("Sending to work on task: {}".format(str(request.json)))
            app.metric_status_worker.task = request.json

            #set task
            return Response(response=request.json,
                        status=200,
                        mimetype="application/json")
        if request.method == 'GET': #will retrieve the current tasks/status of the worker
            return jsonify({
                "status": "success"
            })
        return Response(response=request.json,
                        status=200,
                        mimetype="application/json")

    @app.route("/AUGWOP/config")
    def augwop_config():
        """ Retrieve worker's config
        """
        return app.metric_status_worker.config

@click.command()
@click.option('--augur-url', default='http://localhost:5000/', help='Augur URL')
@click.option('--host', default='localhost', help='Host')
@click.option('--port', default=51263, help='Port')
def main(augur_url, host, port):
    """ Declares singular worker and creates the server and flask app that it will be running on
    """
    app = Flask(__name__)
    #load credentials
    credentials = read_config("Database", use_main_config=1)
    server = read_config("Server", use_main_config=1)
    worker_info = read_config("Workers", use_main_config=1)['metric_status_worker']
    worker_port = worker_info['port'] if 'port' in worker_info else port

    config = { 
            "id": "com.augurlabs.core.metric_status_worker",
            "location": "http://localhost:{}".format(worker_port),
            "broker_port": server['port'],
            "host": credentials["host"],
            "key": credentials["key"],
            "password": credentials["password"],
            "port": credentials["port"],
            "user": credentials["user"],
            "database": credentials["database"],
            "table": "chaoss_metric_status",
            "endpoint": "http://localhost:{}/api/unstable/metrics/status".format(server['port']),
            "type": "string"
        }

    #create instance of the worker
    app.metric_status_worker = MetricStatusWorker(config) # declares the worker that will be running on this server with specified config
    
    create_server(app, None)
    logging.info("Starting Flask App with pid: " + str(os.getpid()) + "...")
    app.run(debug=app.debug, host=host, port=port)
    if app.metric_status_worker._child is not None:
        app.metric_status_worker._child.terminate()
    try:
        requests.post('http://localhost:{}/api/unstable/workers/remove'.format(server['port']), json={"id": config['id']})
    except:
        pass
    logging.info("Killing Flask App: " + str(os.getpid()))
    os.kill(os.getpid(), 9)    


def read_config(section, name=None, environment_variable=None, default=None, config_file='augur.config.json', no_config_file=0, use_main_config=0):
    """
    Read a variable in specified section of the config file, unless provided an environment variable

    :param section: location of given variable
    :param name: name of variable
    """


    __config_bad = False
    if use_main_config == 0:
        __config_file_path = os.path.abspath(os.getenv('AUGUR_CONFIG_FILE', config_file))
    else:        
        __config_file_path = os.path.abspath(os.path.dirname(os.path.dirname(os.getcwd())) + '/augur.config.json')

    __config_location = os.path.dirname(__config_file_path)
    __export_env = os.getenv('AUGUR_ENV_EXPORT', '0') == '1'
    __default_config = { 'Database': {"host": "nekocase.augurlabs.io"} }

    if os.getenv('AUGUR_ENV_ONLY', '0') != '1' and no_config_file == 0:
        try:
            __config_file = open(__config_file_path, 'r+')
        except:
            # logger.info('Couldn\'t open {}, attempting to create. If you have a augur.cfg, you can convert it to a json file using "make to-json"'.format(config_file))
            if not os.path.exists(__config_location):
                os.makedirs(__config_location)
            __config_file = open(__config_file_path, 'w+')
            __config_bad = True


        # Options to export the loaded configuration as environment variables for Docker

        if __export_env:

            export_filename = os.getenv('AUGUR_ENV_EXPORT_FILE', 'augur.cfg.sh')
            __export_file = open(export_filename, 'w+')
            # logger.info('Exporting {} to environment variable export statements in {}'.format(config_file, export_filename))
            __export_file.write('#!/bin/bash\n')

        # Load the config file and return [section][name]
        try:
            config_text = __config_file.read()
            __config = json.loads(config_text)
            if name is not None:
                return(__config[section][name])
            else:
                return(__config[section])

        except json.decoder.JSONDecodeError as e:
            if not __config_bad:
                __using_config_file = False
                # logger.error('%s could not be parsed, using defaults. Fix that file, or delete it and run this again to regenerate it. Error: %s', __config_file_path, str(e))

            __config = __default_config
            return(__config[section][name])

