import os
import boto3
import botocore
import json
from botocore.exceptions import ClientError
import time
import paramiko


def script_commands():
  return """#!/bin/bash
  cd home/ubuntu/
  git clone https://github.com/hugosoftdev/webserver.git
  cd webserver
  chmod +x install.sh
  ./install.sh
  """

def getInstancesIpFromId(ids):
    instances = ec2.describe_instances(
          InstanceIds=ids
    )
    if(len(instances['Reservations']) < 1):
      print('não foi retornado reservations')
      return []
    else:
      intancesIp = [instance['PublicIpAddress'] for instance in instances['Reservations'][0]['Instances']]
      return intancesIp



def create_key_pair(keyPairName):
  exists = check_if_key_pair_exists(keyPairName)
  if(exists):
    deleteKeyPair(keyPairName)
    if os.path.exists("{0}.pem".format(keyPairName)):
      os.remove("{0}.pem".format(keyPairName))
  response = ec2.create_key_pair(KeyName=keyPairName)
  with open("{0}.pem".format(keyPairName), "w") as pemFile:
    pemFile.write(response['KeyMaterial'])
    os.chmod('./{0}.pem'.format(keyPairName), 0o400)


def check_if_key_pair_exists(keyPairName):
  response = ec2.describe_key_pairs()
  keyPairs = response["KeyPairs"]
  exists = False
  for key in keyPairs:
    if(key["KeyName"] == keyPairName):
      exists = True
      break
  return exists

def deleteKeyPair(keyPairName):
  ec2.delete_key_pair(KeyName=keyPairName)


def create_security_group(name):
  exists = check_if_security_group_exists(name)
  if(exists != False):
    return exists
    #delete_security_group(exists)
    #time.sleep(3)
  response = ec2.describe_vpcs()
  vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')
  try:
      response = ec2.create_security_group(GroupName=name,Description='None', VpcId=vpc_id)
      security_group_id = response['GroupId']
      data = ec2.authorize_security_group_ingress(
          GroupId=security_group_id,
          IpPermissions=[
              {'IpProtocol': 'tcp',
              'FromPort': 8888,
              'ToPort': 8888,
              'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
              {'IpProtocol': 'tcp',
              'FromPort': 22,
              'ToPort': 22,
              'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
          ])
      return security_group_id
  except ClientError as e:
      print(e)


def check_if_security_group_exists(name):
  try:
    response = ec2.describe_security_groups()
    for group in response['SecurityGroups']:
      if(group['GroupName'] ==  name):
        return group['GroupId']
    return False
  except ClientError as e:
      print(e)

def delete_security_group(id):
    # Delete security group
  try:
      response = ec2.delete_security_group(GroupId=id)
  except ClientError as e:
      print(e)

def delete_instances():
    print('Getting Instances To Delete')
    running_instances = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:Owner',
                'Values': [
                    'HugaoDaMassa',
                ]
            },
        ]
    )
    if(len(running_instances['Reservations']) > 0):
      instancesId = [instance['InstanceId'] for instance in running_instances['Reservations'][0]['Instances']]
      print('Running instances Id: {0}'.format(instancesId))
      print('Terminating instances')
      response = ec2.terminate_instances(
          InstanceIds=instancesId,
          DryRun=False
      )
      print('Instances deleted')
    else:
      print('No instances to delete')


def create_instances(numberOfInstances, deletePrevious = False):
  # configs
  keyid = os.environ['AWS_ACCESS_KEY']
  secretkey = os.environ['AWS_SECRET_KEY']
  global ec2
  ec2 = boto3.client(
      'ec2',
      region_name='us-east-1',
      aws_access_key_id=keyid,
      aws_secret_access_key=secretkey,
  )

  if(deletePrevious == True):
    delete_instances()

  imageId = "ami-0ac019f4fcb7cb7e6"
  tipo = 't2.micro'
  KeyName = 'HUGO_DA_MASSA'
  create_key_pair(KeyName)
  print('key pairs created')
  security_group_id = create_security_group('teste_fora')
  print('security group created')
  response = ec2.run_instances(
      ImageId=imageId,
      InstanceType= tipo,
      MinCount=numberOfInstances,
      MaxCount=numberOfInstances,
      KeyName=KeyName,
      UserData=script_commands(),
      SecurityGroupIds=[security_group_id],
      TagSpecifications=[{'ResourceType': 'instance','Tags': [{'Key': 'Owner','Value': 'HugaoDaMassa'}]}]
  )
  print('instances created')
  instances = response['Instances']
  createdInstancesId = [instance['InstanceId'] for instance in instances]
  time.sleep(1)

  print('waiting okay status')
  # Also wait status checks to complete
  waiter = ec2.get_waiter('instance_status_ok')
  waiter.wait(InstanceIds=createdInstancesId)
  print('instances status okay')
  
  print('Retrieving IPs')
  InstanceIps = getInstancesIpFromId(createdInstancesId)
  print('Done')
  return InstanceIps

  
