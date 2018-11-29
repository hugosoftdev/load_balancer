import json
import sys
import os
from flask import Flask, make_response, request, Response
import requests
from threading import Thread
from time import sleep
from random import randint
from criar_instancia import create_instances

def HealthCheckThread(ips):
  healthyIps = ips
  for i in ips:
    try:
      requests.get('http://{0}:8888/healthcheck'.format(i), timeout=6)
    except requests.exceptions.Timeout as e:
      print("Unhealthy instance detected, replacing it...")
      healthyIps = [ip for ip in ips if ip != i]
      newIp = create_instances(1,False)
      healthyIps.append(newIp[0])
      global InstancesIP
      InstancesIP = healthyIps
  sleep(4)
  HealthCheckThread(healthyIps)
    


def create_app():
    app = Flask(__name__)
    def run_on_start(*args, **argv):
      if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # do something only once, before the reloader
        global InstancesIP
        numberofInstances = 3
        try:
          f = open('./number_of_instances.txt')
          line = f.readline()
          numberofInstances = int(line)
          f.close()
        except:
          print('file "number_of_instances.txt" not found or text its not subscriptable to an int')
        print('Instances to be up {0}'.format(numberofInstances))
        InstancesIP = create_instances(numberofInstances, True)
        print("Instances IP: ", InstancesIP)
        thread = Thread(target=HealthCheckThread, args=(InstancesIP, ))
        thread.start()
      
    run_on_start()
    return app


app = create_app()

def forward(request):
    if(len(InstancesIP) < 1):
      content = json.dumps({"error": "No insntaces Available"})
      status = 404
      return  make_response(content, status, {'Content-Type': 'application/json'})
    endpoint = request.url.split('8888')[1]
    choosenIp = InstancesIP[randint(0, len(InstancesIP)-1)]
    resp = requests.request(
        method=request.method,
        url='http://{0}:8888{1}'.format(choosenIp,endpoint),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
      )
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response


@app.route('/task', methods=['POST'])
def create_task():
   return forward(request)


@app.route('/task/<int:task_id>', methods=['PUT'])
def update_task(task_id):
  return forward(request)


@app.route('/task', methods=['GET'])
def read_tasks():
  return forward(request)


@app.route('/task/<int:task_id>', methods=['GET'])
def read_task(task_id):
  return forward(request)


@app.route('/task/<int:task_id>', methods=['DELETE'])
def remove_tasks(task_id):
  return forward(request)
