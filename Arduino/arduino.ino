#include <WiFi.h>
#include <PubSubClient.h>
#include <Servo.h>
#include <ArduinoJson.h>

// WiFi 配置信息
const char* ssid = "SBLYK";
const char* password = "qw123456er";

// MQTT 服务器设置
const char* mqtt_server = "a3863654.ala.dedicated.aliyun.emqxcloud.cn";
const int mqtt_port = 1883;
const char* mqtt_topic_sub = "environment/response"; // 订阅的主题
const char* mqtt_topic_pub = "arduino/signal";       // 发布的主题
const char* mqtt_client_id = "arduino_client";
const char* mqtt_username = "Memory";
const char* mqtt_password = "qw123456er";

// 设备引脚定义
const int redLED = 6;       // 红色 LED 引脚
const int greenLED = 5;     // 绿色 LED 引脚
const int servoPin = 9;     // 舵机引脚
const int buzzerPin = 10;   // 蜂鸣器引脚
const int buttonLED = 2;    // 控制LED的按钮引脚
const int buttonBuzzer = 4; // 蜂鸣器按钮引脚
const int buttonMQTT = 7;   // MQTT 按钮引脚

WiFiClient espClient;
PubSubClient client(espClient);
Servo myServo;

int mqttPressCount = 0;     // 记录MQTT按钮按下次数

bool ledStatus = true;      // 默认LED根据信号响应
unsigned long ledOffTime = 0;

bool buzzerStatus = true;   // 默认蜂鸣器根据信号响应
bool buzzerState = false;   // 当前蜂鸣器状态（开启或关闭）
unsigned long buzzerOffTime = 0;

void setup() {
  Serial.begin(115200);

  // 初始化设备
  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(buttonLED, INPUT_PULLUP);
  pinMode(buttonBuzzer, INPUT_PULLUP);
  pinMode(buttonMQTT, INPUT_PULLUP);

  myServo.attach(servoPin);
  myServo.write(0);

  connectWiFi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  handleButtonActions();
  restoreLEDandBuzzer();
}

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(mqtt_client_id, mqtt_username, mqtt_password)) {
      Serial.println("connected");
      client.subscribe(mqtt_topic_sub);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    Serial.print("deserializeJson() failed: ");
    Serial.println(error.f_str());
    return;
  }

  const char* signal = doc["signal"];

  if (strcmp(signal, "#1") == 0) {
    if (ledStatus) {
      digitalWrite(redLED, HIGH);
      digitalWrite(greenLED, LOW);
    }
    Serial.println("Signal #1 received. Fire.");
    myServo.write(180); // 舵机旋转
    if (buzzerStatus) {
      buzzerState = true; // 保持蜂鸣器开启
      tone(buzzerPin, 1000);
    }
  } else if (strcmp(signal, "#2") == 0) {
    if (ledStatus) {
      digitalWrite(redLED, LOW);
      digitalWrite(greenLED, HIGH);
    }
    Serial.println("Signal #2 received. Normal.");
    myServo.write(0);
    buzzerState = false; // 关闭蜂鸣器
    noTone(buzzerPin);
  } else if (strcmp(signal, "#3") == 0) {
    if (ledStatus) {
      digitalWrite(redLED, HIGH);
      digitalWrite(greenLED, HIGH);
    }
    Serial.println("Signal #3 received. Abnormal.");
    myServo.write(180);
    buzzerState = false; // 关闭蜂鸣器
    noTone(buzzerPin);
  }
}

void handleButtonActions() {
  static unsigned long lastButtonTimeLED = 0;
  static unsigned long lastButtonTimeBuzzer = 0;
  static unsigned long lastButtonTimeMQTT = 0;

  if (digitalRead(buttonLED) == LOW && millis() - lastButtonTimeLED > 2000) {
    ledStatus = false;
    digitalWrite(redLED, LOW);
    digitalWrite(greenLED, LOW); // 关闭LED
    Serial.println("Turn off LEDs");
    ledOffTime = millis() + 10000; // 10秒后重启
    lastButtonTimeLED = millis();
  }

  if (digitalRead(buttonBuzzer) == LOW && millis() - lastButtonTimeBuzzer > 2000) {
    buzzerStatus = false;
    buzzerState = false; // 禁止蜂鸣器
    noTone(buzzerPin);
    Serial.println("Turn off the buzzer.");
    buzzerOffTime = millis() + 10000; // 10秒后重启
    lastButtonTimeBuzzer = millis();
  }

  if (digitalRead(buttonMQTT) == LOW && millis() - lastButtonTimeMQTT > 2000) {
    mqttPressCount++;
    StaticJsonDocument<256> doc;
    if (mqttPressCount % 2 == 0) {
      doc["signal"] = "#4"; // 发送信号#4
      Serial.println("Turn on sensor, send signal #4.");
    } else {
      doc["signal"] = "#5"; // 发送信号#5
      Serial.println("Switch off sensor, send signal #5.");
    }
    char buffer[256];
    size_t n = serializeJson(doc, buffer);
    client.publish(mqtt_topic_pub, buffer, n);
    lastButtonTimeMQTT = millis();
  }
}

void restoreLEDandBuzzer() {
  if (!ledStatus && millis() > ledOffTime) {
    digitalWrite(redLED, LOW);
    digitalWrite(greenLED, HIGH); // 重启LED，默认绿色
    Serial.println("LEDs restored");
    ledStatus = true;
  }

  if (!buzzerStatus && millis() > buzzerOffTime) {
    Serial.println("Buzzer restored");
    buzzerStatus = true;
  }
}
