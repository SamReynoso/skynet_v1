import os
import time
import socket
import sqlite3
import paho.mqtt.client as paho

from paho.mqtt.enums import CallbackAPIVersion
from common.models import MqttPerams
from typing import Optional


def mqtt_connect(perams: MqttPerams) -> Optional[paho.Client]:
    client = paho.Client(CallbackAPIVersion.VERSION2)
    try:
        if client.connect(perams.addr, perams.port1, perams.port2) != 0:
            print('Mqtt connection failed')
            return
    except ConnectionRefusedError:
        print('Connection refused, make sure the mqtt broker is running')
        return
    return client


def database_connection():
    path = 'data/database/history.db'
    if os.path.isfile(path):
        conn = sqlite3.connect(path)
        return conn

    else:
        raise FileNotFoundError


class ServerSocket:
    path = 'data/programfiles/socket'

    def __init__(self):
        try:
            os.unlink(self.path)
        except OSError:
            if os.path.exists(self.path):
                raise OSError
        self.uni = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.uni.bind(self.path)
        self.uni.settimeout(3)

    def close(self):
        self.uni.close()
        try:
            os.unlink(self.path)
        except OSError:
            if os.path.exists(self.path):
                raise OSError

    def recv(self):
        try:
            data = self.uni.recv(1024).decode()
            if data == 'done':
                self.close()
                return
            return data
        except Exception as e:
            print(e)


def send_wrapper(func, path):
    uni = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    count = 0
    while True:
        if os.path.exists(path):
            try:
                uni.connect(path)
                func(uni)
                uni.send('done'.encode())
                uni.close()
                return
            except ConnectionRefusedError:
                if count == 3:
                    print('uni_connect: ConnectionRefusedError: exiting')
                    return
        if count == 2:
            print("File descriptor at 'path' does not exists")
            return
        count += 1
        time.sleep(1)


