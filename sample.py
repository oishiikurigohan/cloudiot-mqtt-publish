#!/usr/bin/env python

import os
import datetime
import ssl
import time
import jwt
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import threading
import serial

# Cloud IoT Core接続情報
# 適宜変更して下さい。
PROJECT_ID = 'test-project-001-xxxxxx'
CLOUD_REGION = 'asia-east1'
REGISTRY_ID = 'reg001'
DEVICE_ID = 'raspberry001'
ALGORITHM = 'RS256'
PRIVATE_KEY_FILE = 'rsa_private.pem'
CA_CERTS = 'roots.pem'
MQTT_BRIDGE_HOSTNAME = 'mqtt.googleapis.com'
MQTT_BRIDGE_PORT = 8883

# Raspberry pi GPIO
BUTTON = 23
LED = 24

# GCPへ送信する位置情報のリスト
location_list = []

# Raspberry pi シリアル通信ポート
serial_port = None

# GCP送信フラグ
send_location_info = False


# mqtt client callback
def on_connect(unused_client, unused_userdata, unused_flags, rc):
    print('on_connect', mqtt.connack_string(rc))

def on_disconnect(unused_client, unused_userdata, rc):
    print('on_disconnect', mqtt.error_string(rc))

def on_publish(unused_client, unused_userdata, unused_mid):
    print('on_publish:', unused_mid)

def on_message(unused_client, unused_userdata, message):
    print('on_message')

# 位置情報リストが存在する場合、1秒に1件ずつpublishする。
def mqtt_publish():

    mqtt_topic = '/devices/{}/{}'.format(DEVICE_ID, 'events')
    client_id = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(PROJECT_ID, CLOUD_REGION, REGISTRY_ID, DEVICE_ID)
    client = mqtt.Client(client_id=client_id)

    # Google Cloud IoT Coreでは、ユーザー名フィールドは無視され、
    # パスワードフィールドはJWTを送信してデバイスを認証するために使用されます。
    token = {
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=20),
        'aud': PROJECT_ID
    }

    with open(PRIVATE_KEY_FILE, 'r') as f:
        private_key = f.read()

    password = jwt.encode(token, private_key, algorithm=ALGORITHM)
    client.username_pw_set(username='unused',password=password)

    # Enable SSL/TLS support.
    client.tls_set(ca_certs=CA_CERTS, tls_version=ssl.PROTOCOL_TLSv1_2)

    # Register message callbacks.
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    # Connect to the Google MQTT bridge.
    client.connect(MQTT_BRIDGE_HOSTNAME, MQTT_BRIDGE_PORT)

    # Publish message MQTT topic.
    client.loop_start()
    while True:
        try:
            client.publish(mqtt_topic, location_list.pop(0), qos=1)
        except IndexError:
            pass
        time.sleep(1)


# GPSモジュールからシリアル通信で位置情報を取得する。
def get_location_info():

    global serial_port
    serial_port = serial.Serial('/dev/serial0', 9600, timeout=10)

    while True:
        try:
            data = serial_port.readline().decode('utf-8')
            if data.startswith("$GPRMC") and send_location_info:
                sData = data.split(',')
                pData = ','.join([DEVICE_ID, sData[1], sData[3], sData[5]])
                print('append', pData)
                location_list.append(pData)
        except UnicodeDecodeError:
            pass
        time.sleep(0.2)


# LEDのON/OFFと、位置情報の送信ステータスを切り替える。
# LEDがONの場合は位置情報をGCPへ送信する。
# LEDがOFFの場合は送信しない。
def toggleLED(self):
    global send_location_info
    send_location_info = not GPIO.input(LED)
    GPIO.output(LED, send_location_info)


def main():

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(LED, GPIO.OUT, initial=GPIO.LOW)
    GPIO.add_event_detect(BUTTON, GPIO.RISING, toggleLED, bouncetime=500)

    mqtt_publish_thread = threading.Thread(target=mqtt_publish, args=())
    mqtt_publish_thread.daemon = True
    mqtt_publish_thread.start()
    
    get_location_info_thread = threading.Thread(target=get_location_info, args=())
    get_location_info_thread.daemon = True
    get_location_info_thread.start()

    mqtt_publish_thread.join()
    get_location_info_thread.join()


if __name__ == '__main__':

    try:
        main()

    except KeyboardInterrupt:
        serial_port.close()
        GPIO.cleanup()
        print(' === end ===')
