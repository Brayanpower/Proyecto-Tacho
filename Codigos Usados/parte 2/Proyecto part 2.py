from machine import Pin, ADC, SoftI2C
from ssd1306 import SSD1306_I2C
import time
import network
from umqtt.simple import MQTTClient

# Configuración de los pines
pir_pin = Pin(5, Pin.IN)    # Pin del sensor PIR
relay_pin = Pin(22, Pin.OUT)  # Pin de control del relé
analog_pin = 36  # Pin analógico utilizado en tu ESP32
MQ_pin = 32  # Pin del sensor MQ
buzzer_activo_pin = Pin(18, Pin.OUT)

# Configuración del I2C para la pantalla OLED
i2c = SoftI2C(scl=Pin(23), sda=Pin(21))
oled = SSD1306_I2C(128, 64, i2c)

# Configuración del pin analógico
adc = ADC(Pin(analog_pin))
adc.atten(ADC.ATTN_11DB)

# Parámetros para conectarnos a un broker MQTT
MQTT_CLIENT_ID = ""
MQTT_BROKER = "192.168.187.135"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_TOPIC_GAS = "utng/Proyecto/gas"
MQTT_TOPIC_PIR = "utng/Proyecto/movimiento"
MQTT_TOPIC_REL = "utng/Proyecto/relay"
MQTT_PORT = 1883

# Función encargada de encender o apagar el relé según el mensaje recibido
def llegada_mensaje(topic, msg):
    print("Mensaje:", msg)
    if topic == MQTT_TOPIC_REL:
        if msg == b'true':
            relay_pin.on()
        elif msg == b'false':
            relay_pin.off()

# Función para suscribirse al broker MQTT y configurar el cliente
def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID,
                        MQTT_BROKER, 
                        user=MQTT_USER,
                        password=MQTT_PASSWORD)
    client.set_callback(llegada_mensaje)
    client.connect()
    client.subscribe(MQTT_TOPIC_GAS)
    client.subscribe(MQTT_TOPIC_PIR)
    client.subscribe(MQTT_TOPIC_REL)
    print("Conectado a %s, en el topico %s"%(MQTT_BROKER, MQTT_TOPIC_GAS))
    print("Conectado a %s, en el topico %s"%(MQTT_BROKER, MQTT_TOPIC_PIR))
    print("Conectado a %s, en el topico %s"%(MQTT_BROKER, MQTT_TOPIC_REL))
    return client

# Función para conectar a la red WiFi
def conectar_wifi():
    print("Conectando a WiFi", end="")
    sta_if = network.WLAN(network.STA_IF)
    sta_if.active(True)
    sta_if.connect('Adrian', '123456ad')
    while not sta_if.isconnected():
        print(".", end="")
        time.sleep(0.1)
    print("  Connected!  ")

# Conectar a wifi
conectar_wifi()
# Subscripción a un broker mqtt
client = subscribir()

# Función para precalentar el sensor MQ
def precalentar_sensor():
    print("El sensor de gas se está precalentando")
    time.sleep(20)  # Espera a que el sensor se caliente durante 20 segundos
    
def generar_sonido_activo():
    buzzer_activo_pin.on()
    time.sleep(0.1)  # Duración del sonido (0.5 segundo en este caso)
    buzzer_activo_pin.off()

# Función para leer el valor del sensor MQ
def leer_valor_MQ():
    return adc.read()

# Función para leer el estado del sensor PIR
def leer_estado_PIR():
    return pir_pin.value()

# Función principal
def main():
    precalentar_sensor()  # Precalentar el sensor MQ
    
    # Inicializar el estado del sensor PIR
    pir_pin.value(0)
    
    while True:
        # Leemos el estado del sensor PIR
        pir_value = leer_estado_PIR()
        print("Valor del sensor PIR:", pir_value)
        
        # Realizamos acciones en función del estado del sensor PIR
        if pir_value == 1:
            print("Movimiento detectado")
            relay_pin.value(1)  # Activar el relé (cierra el circuito)
            generar_sonido_activo()
            client.publish(MQTT_TOPIC_REL, b'1')
            client.publish(MQTT_TOPIC_PIR, b'1') # Enviar estado del PIR
            time.sleep(30)  # Espera 30 segundos antes de volver a comprobar
        else:
            print("Sin movimiento")
            relay_pin.value(0)  # Desactivar el relé (abre el circuito)
            client.publish(MQTT_TOPIC_REL, b'0')
            client.publish(MQTT_TOPIC_PIR, b'0') # Enviar estado del PIR
            time.sleep(1)  # Espera 1 segundo antes de volver a comprobar
        
        # Leemos el valor del sensor MQ y realizamos acciones en función de él
        MQ_valor = leer_valor_MQ()
        print("Valor del sensor MQ:", MQ_valor)
        client.publish(MQTT_TOPIC_GAS, str(MQ_valor))
        
        # Actualizamos la pantalla OLED con el valor leído del sensor MQ
        oled.fill(0)  # Limpiar pantalla
        oled.text("Concentracion", 0, 0)
        oled.text("de gas:", 0, 10)
        oled.text(str(MQ_valor), 0, 20)
        oled.show()
        
        # Realizamos acciones según la concentración de gas
        if MQ_valor > 1000:
            print("Concentración alta de gas")
        elif 500 < MQ_valor <= 1000:
            print("Concentración moderada de gas")
        else:
            print("Concentración baja de gas")
        
        time.sleep(1)  # Espera 1 segundo antes de volver a comprobar

# Ejecutar la función principal
if _name_ == "_main_":
    main()