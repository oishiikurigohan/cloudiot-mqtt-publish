# cloudiot-mqtt-publish
Raspberry piに接続したGPSモジュールから位置情報を取得し、mqttでGoogle Cloud IoT CoreにPublishします。

事前にCloud IoT Coreのregistry作成やdevice登録、  
Cloud Pub/Subのtopicやsubscriptionを作成する必要があります。  
詳細は[Google Cloud公式ドキュメント](https://cloud.google.com/iot/docs/quickstart?hl=ja)をご参照下さい。  
Raspberry piの設定やパーツの配線については当方ブログ([1](http://www.kurigohan.com/article/20200521_raspi_to_gcp_iot_core.html), [2](http://www.kurigohan.com/article/20200526_raspberry_pi_tact_switch.html))にてご紹介しております。
  
***
  
依存パッケージのインストール(不要な物があったらスミマセン)
```
$ pip3 install -r requirements.txt
```
  
RSA鍵ペアを生成、公開鍵はCloud IoT Coreのdeviceに登録
```
$ openssl req -x509 -newkey rsa:2048 -days 3650 -keyout rsa_private.pem -nodes -out rsa_cert.pem -subj "/CN=unused"
```
  
SSL/TLSのroot証明書を取得
```
$ wget https://pki.google.com/roots.pem
```
  
実行
```
$ python3 sample.py
```
