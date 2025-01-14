import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
class MyDHT11():
    def __init__(self, pin=18, broker_address="localhost", port=1883):
        self.history_humidity = 0
        self.history_temperature = 0
        self.tmp = [] # 用来存放读取到的数据
        self.data = pin # DHT11的data引脚连接到的树莓派的GPIO引脚，使用BCM编号
        self.broker_address = broker_address # MQTT broker的地址
        self.port = port # MQTT broker的端口
        self.mqtt_client = mqtt.Client() # 初始化MQTT客户端
        self.mqtt_client.connect(self.broker_address, self.port, 60)  # 连接到MQTT broker
       # 订阅主题（可选，根据需求决定是否订阅）
       # self.mqtt_client.subscribe("some/topic")
       self.a, self.b = 0, 0
    def delayMicrosecond(self, t): # 微秒级延时函数（这里仍然使用不精确的方法，建议替换为更精确的方法）
       time.sleep(t / 1000000.0) # 直接使用time.sleep来模拟微秒级延时（注意：这实际上并不精确）
    def DHT11(self):
        #elf.DHT11()
        # 数据处理逻辑保持不变...
        # 发送MQTT消息
        self.send_mqtt_message(humidity, temperature)
        return self.history_temperature, self.history_humidity
    def send_mqtt_message(self, humidity, temperature):
        # 判断温度并发送相应的MQTT消息
        if temperature >= 50:
            self.mqtt_client.publish("home/temperature/alert", "Fire alert! Temperature: {:.1f}°C".format(temperature))
        elif temperature <= 8:
            self.mqtt_client.publish("home/temperature/alert", "Low temperature alert! Temperature: {:.1f}°C".format(temperature))
        elif temperature >= 40:
            self.mqtt_client.publish("home/temperature/alert", "High temperature alert! Temperature: {:.1f}°C".format(temperature))
        # 可以添加更多的消息类型或逻辑
    def cleanup(self):
        # 清理GPIO设置和断开MQTT连接
        GPIO.cleanup()
        self.mqtt_client.disconnect()
if __name__ == "__main__":
    mDht11 = MyDHT11(18)
    try:
        while True:
            t, h = mDht11.read_dht11()
            print(t, h)
            time.sleep(3)
    except KeyboardInterrupt:
        # 捕获Ctrl+C以进行清理
        mDht11.cleanup() ...（DHT11的读取逻辑保持不变）
    def read_dht11(self):
        GPIO.setmode(GPIO.