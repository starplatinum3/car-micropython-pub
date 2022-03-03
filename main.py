
import time
import machine
from machine import Pin,PWM
import _thread
import micropython
import main
from machine import ADC
import utime
from umqtt.simple import MQTTClient
import ubinascii
import network
import dht
from machine import Timer
from machine import UART
# right wheel
p1 =Pin(27 ,Pin.OUT)
p2 =Pin(14 ,Pin.OUT)
infra_red_front=Pin(23)
infra_red_behind=Pin(22)
# left wheel
p3 =Pin(21 ,Pin.OUT)
p4 =Pin(33 ,Pin.OUT)
v_left =Pin(16)
v_right =Pin(17)
#
v_right_pwm =PWM(Pin(17) ,freq=2000 ,duty=512  )  # pwm 速度 right
v_left_pwm =PWM(Pin(16) ,freq=2000,duty=512  )  # pwm 速度 left
led=Pin(32)

led_pwm=PWM(led)


def Forward_speed_regulation(which,speed):#正转调速，轮胎

  if which=='left':
    p3.value(1)
    p4.value(0)
    v_left_pwm.duty(speed)
  else:
    p1.value(1)
    p2.value(0)  
    v_right_pwm.duty(speed)
 
def Back_speed_regulation(which,speed):
  if which=='left':
    p3.value(0)
    p4.value(1)   
    v_left_pwm.duty(speed)
  else:
    p1.value(0)
    p2.value(1) 
    v_right_pwm.duty(speed)

 #全速 
def turn_left():
  Back_speed_regulation('left',1023)
  Forward_speed_regulation('right',1023)
def turn_right():
  Forward_speed_regulation('left',1023)
  Back_speed_regulation('right',1023)
  
def back():
  Back_speed_regulation('left',1023)
  Back_speed_regulation('right',1023)
def forward():
  Forward_speed_regulation('left',1023)
  Forward_speed_regulation('right',1023)
  
  #控制前进的速度
def turn_left_with_speed(speed):
  Back_speed_regulation('left',speed)
  Forward_speed_regulation('right',speed)
def turn_right_with_speed(speed):
  Forward_speed_regulation('left',speed)
  Back_speed_regulation('right',speed)
  
def back_with_speed(speed):
  if speed==1000:
    Back_speed_regulation('left',1023)
    Back_speed_regulation('right',1023)
  elif speed==750:
    Back_speed_regulation('left',speed+170)
    Back_speed_regulation('right',speed)
  elif speed==500:
    Back_speed_regulation('left',speed+190)
    Back_speed_regulation('right',speed)
  elif speed==250:
    Back_speed_regulation('left',speed+130)
    Back_speed_regulation('right',speed)
  else:
    Back_speed_regulation('left',speed)
    Back_speed_regulation('right',speed)
def forward_with_speed(speed):
  if speed==1000:
   
    Forward_speed_regulation('left',1023)
    Forward_speed_regulation('right',1023)
  elif speed==750:
    Forward_speed_regulation('left',speed+170)
    Forward_speed_regulation('right',speed)
  elif speed==500:
    Forward_speed_regulation('left',speed+190)
    Forward_speed_regulation('right',speed)
  elif speed==250:
    Forward_speed_regulation('left',speed+130)
    Forward_speed_regulation('right',speed)
    
  else:
    Forward_speed_regulation('left',speed)
    Forward_speed_regulation('right',speed)
 #控制轮胎
def full_speed_forward_tyre(which):
    if which=='left':
        p3.value(1)
        p4.value(0)
        v_left.on()
    else:
        p1.value(1)
        p2.value(0)
        v_right.on()

def full_speed_back_tyre(which):
    if which=='left':
        p3.value(0)
        p4.value(1)
        v_left.on()
    else:
        p1.value(0)
        p2.value(1)
        v_right.on()
#控制两个轮胎前进就是控制小车前进了
def full_speed_forward():
    full_speed_forward_tyre('left')
    full_speed_forward_tyre('right')
    
def full_speed_back():
    full_speed_back_tyre('left')
    full_speed_back_tyre('right')
   
def full_speed_left():
    full_speed_back_tyre('left')
    full_speed_forward_tyre('right')

def full_speed_right():
    full_speed_forward_tyre('left')
    full_speed_back_tyre('right')

def brake():
    p1.off()
    p2.off()
    p3.off()
    p4.off()



SERVER = '111.111.111'  # MQTT服务器
CLIENT_ID = ubinascii.hexlify(machine.unique_id())  # 获取ESP32的ID
SUBSCRIBE_TOPIC = b'1111'  # TOPIC的ID
username = '111'  # 账号
password = '1111'  # 密码
PUBLISH_TOPIC =b'111111'

#向服务器发信息
def send_msg(msg):
  client.publish(PUBLISH_TOPIC ,msg)
#设置服务器
def set_client():
  global client
  client = MQTTClient(CLIENT_ID, SERVER, 0, username, password, 60)
  client.set_callback(mqtt_callback)
  client.connect()
  client.subscribe(SUBSCRIBE_TOPIC)
state=b'0'
car_state=b'brake'
car_speed=0
#把byte类型的信号转化成string，并且提取速度的值
def change(byte):
  dir=['forward','back','left','right'] #把四个方向的文字都去掉
  car_word=byte.decode()
  for i in dir:
    car_word=car_word.replace(i,'')
  return int(car_word)
#接到信号后的反应
def mqtt_callback(topic, msg):
# 关于global，python不能直接改变全局变量，因此要在函数里生命这个变量是全局的，然后才可以改变他，并且，此改变是造福（或者作恶）于全局的，并不只是作用在函数中

    global state,car_state,car_speed
    print(msg)
    if msg==b'brake':  
        print('brake')
        send_msg('brake')
        brake()
        car_state=b'brake'
    elif b'left' in msg:
        car_speed=change(msg)#要把bytes的信号转化成string，而且把其中的速度提取一下
        print('turn left')
        
        send_msg('turn left '+str(car_speed))
        
        #full_speed_left()
        turn_left_with_speed(car_speed)
    elif b'right' in msg:
        car_speed=change(msg)
        print('turn right')
        send_msg('turn right '+str(car_speed))
        turn_right_with_speed(car_speed)
    elif b'back' in msg:
        car_speed=change(msg)
        if infra_red_behind.value()==0:
            print('back')
            send_msg('back '+str(car_speed))
            
            back_with_speed(car_speed)
            car_state=b'back'
            
        else:
            send_msg('Cliff there, you want me to die?')
            print('Cliff there, you want me to die?')
            brake()
            car_state=b'brake'
      
       
    elif b'forward' in msg:
        car_speed=change(msg)
        
        if infra_red_front.value()==0:#只有红外说可以走，才走
            print('forward')
            send_msg('forward '+str(car_speed))
            #forward()
            forward_with_speed(car_speed)
            car_state=b'forward'
            
        else:
            send_msg('Cliff over there, you want me to die?')
            print('Cliff over there, you want me to die?')
            brake()
            car_state=b'brake'

#检查mqtt上的信号
def check():
    print('check')
    global car_state
    while True:
        # 查看是否有数据传入
        # 有的话就执行 mqtt_callback
        if infra_red_behind.value()==1:#如果红外状态是不能后退并且小车状态是后退状态，会直接刹车
          if car_state==b'back':
            brake()
            print('brake')
        if infra_red_front.value()==1:
          if car_state==b'forward':
            brake()
            print('brake')
            
        client.check_msg()
        utime.sleep_ms(100)
#连接wifi
def connect_to_wifi():
    wifi = network.WLAN(network.STA_IF)  # 创建一个网络接口
    if not wifi.isconnected():
        wifi.active(True  )  # 激活网络接口
        wifi.disconnect(  )  # 中断之前连接的wifi
        wifi.connect('1111' ,'1111')  # 输入账号密码连接网络
    while(wifi.ifconfig()[0 ]=='0.0.0.0'):
        time.sleep(1)
    print(wifi.ifconfig())

#初始化，连接wifi，服务器，开始检查信号
def init():
  print('connecting to the car')
  connect_to_wifi()
  set_client()
  print('connecting completed')
  send_msg('are you my master?')
  led_pwm.duty(20)
  check()
led_pwm.duty(0)
init()
