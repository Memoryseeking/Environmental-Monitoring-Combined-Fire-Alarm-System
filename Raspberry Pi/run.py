import json
import time
import RPi.GPIO as GPIO
import aliLink
import mqttd
from dht11 import MyDHT11

GPIO.setmode(GPIO.BCM)

# 初始化DHT11传感器
mDht11 = MyDHT11(26)  # 引脚26为示例

# 阿里云设备信息
ProductKey = '<Your ProductKey>'
DeviceName = '<Your DeviceName>'
DeviceSecret = '<Your DeviceSecret>'
POST = '/sys/<Your ProductKey>/<Your DeviceName>/thing/event/property/post'
POST_REPLY = '/sys/<Your ProductKey>/<Your DeviceName>/thing/event/property/post_reply'
SET = '/sys/<Your ProductKey>/<Your DeviceName>/thing/service/property/set'

# EMQX服务器配置
EMQX_HOST = "<Your EMQX Host>"
EMQX_PORT = 1883
EMQX_TOPIC_SUB = "<Your Subscription Topic>"
EMQX_TOPIC_PUB = "<Your Publication Topic>"


# 初始化状态变量
sensors_active = False

def activate_sensors():
    global sensors_active
    sensors_active = True
    print("Sensors activated.")

def deactivate_sensors():
    global sensors_active
    sensors_active = False
    print("Sensors deactivated.")

# 处理阿里云下发的消息
def on_aliyun_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        signal = payload['params'].get('signal', '')
        if signal == '#4':
            activate_sensors()
        elif signal == '#5':
            deactivate_sensors()
        print(f"Aliyun message received: {signal}")
    except Exception as e:
        print(f"Error processing Aliyun message: {e}")

# EMQX消息处理
def on_emqx_message(client, userdata, msg):
    try:
        # 解析JSON信号
        payload = json.loads(msg.payload)
        signal = payload.get('signal', '')
        if signal == '#4':
            activate_sensors()
        elif signal == '#5':
            deactivate_sensors()
        print(f"EMQX message received: {signal}")
    except json.JSONDecodeError:
        print("Error decoding JSON message from EMQX.")
    except Exception as e:
        print(f"Error processing EMQX message: {e}")

# 阿里云连接配置
Server, ClientId, userNmae, Password = aliLink.linkiot(DeviceName, ProductKey, DeviceSecret)
mqtt_aliyun = mqttd.MQTT(Server, ClientId, userNmae, Password)
mqtt_aliyun.subscribe(SET)
mqtt_aliyun.begin(on_aliyun_message, lambda *args: print("Connected to Aliyun"))

# EMQX连接配置
mqtt_emqx = mqttd.MQTT(EMQX_HOST, "emqx_client", username="Memory", password="qw123456er")
mqtt_emqx.subscribe(EMQX_TOPIC_SUB)
mqtt_emqx.begin(on_emqx_message, lambda *args: print("Connected to EMQX"))

# 主循环
try:
    while True:
        time.sleep(10)  # 每10秒上报一次

        if sensors_active:
            # 读取DHT11数据
            dht11_temp, dht11_humi = mDht11.read_dht11()
            print(f"Temperature: {dht11_temp}°C, Humidity: {dht11_humi}%")

            # 构建阿里云上报数据
            data_to_aliyun = {
                'dht11temp': dht11_temp,
                'dht11humi': dht11_humi
            }
            mqtt_aliyun.push(POST, aliLink.Alink(data_to_aliyun))

            # 发送信号到EMQX
            if dht11_temp > 45 and dht11_humi < 30:
                print("Fire, sending signal #1")
                mqtt_emqx.push(EMQX_TOPIC_PUB, json.dumps({'signal': '#1'}))
            elif 30 < dht11_temp <= 45 and 40 < dht11_humi <= 70:
                print("Normalcy, sending signal #2")
                mqtt_emqx.push(EMQX_TOPIC_PUB, json.dumps({'signal': '#2'}))
            else:
                print("Exceptions, sending signal #3")
                mqtt_emqx.push(EMQX_TOPIC_PUB, json.dumps({'signal': '#3'}))
        else:
            print("Sensors are deactivated, skipping data collection.")

except KeyboardInterrupt:
    print("Exiting...")
    GPIO.cleanup()
except Exception as e:
    print(f"Unexpected error: {e}")
    GPIO.cleanup()
