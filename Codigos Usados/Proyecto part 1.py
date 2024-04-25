from machine import Pin, ADC
import time
import network
from umqtt.simple import MQTTClient

# Define los pines GPIO a los que están conectados los LEDs
led_rojo_pin = 16  # Puedes ajustar este número según la configuración de tu hardware
led_verde_pin = 17  # Puedes ajustar este número según la configuración de tu hardware
# Configuración de los pines
relay_pin = Pin(22, Pin.OUT)  # Pin de control del relé

# Definir los pines
PIN_FIRE_ANALOG = 14  # 9 Usar el pin 34 para ESP32
PIN_FIRE_DIGITAL = 4

# Inicializa los pines GPIO para los LEDs
led_rojo = Pin(led_rojo_pin, Pin.OUT)
led_verde = Pin(led_verde_pin, Pin.OUT)

# Inicializa el pin ADC para el fotoresistor
pin_fotoresistor = 34  # Puedes ajustar este número según la configuración de tu hardware
adc = ADC(Pin(pin_fotoresistor))
adc.atten(ADC.ATTN_11DB)  # Establece la atenuación del ADC para 11dB

# Configurar el pin del sensor de fuego como entrada
fire_digital = Pin(PIN_FIRE_DIGITAL, Pin.IN)

# Parámetros para conectarnos a un broker MQTT
MQTT_CLIENT_ID = ""
MQTT_BROKER = "192.168.187.135"
MQTT_USER = ""
MQTT_PASSWORD = ""
MQTT_TOPIC_LLAMA = "utng/Proyecto/llama"
MQTT_TOPIC_RELAY = "utng/Proyecto/relay-2"
MQTT_TOPIC_RGB = "utng/Proyecto/rgb"
MQTT_TOPIC_PHOTORESISTOR = "utng/Proyecto/photo"
MQTT_PORT = 1883

# Función encargada de encender o apagar el LED verde según el mensaje recibido
def llegada_mensaje(topic, msg):
    print("Mensaje:", msg)
    if msg == b'true':
        encender_led_verde()
    elif msg == b'false':
        apagar_led_verde()

# Función para suscribirse al broker MQTT y configurar el cliente
def subscribir():
    client = MQTTClient(MQTT_CLIENT_ID,
                        MQTT_BROKER, 
                        user=MQTT_USER,
                        password=MQTT_PASSWORD)
    client.set_callback(llegada_mensaje)
    client.connect()
    client.subscribe(MQTT_TOPIC_LLAMA)
    print("Conectado a %s, en el topico %s"%(MQTT_BROKER, MQTT_TOPIC_LLAMA))
    client.subscribe(MQTT_TOPIC_RELAY)
    print("Conectado a %s, en el topico %s"%(MQTT_BROKER, MQTT_TOPIC_RELAY))
    client.subscribe(MQTT_TOPIC_RGB)    
    print("Conectado a %s, en el topico %s"%(MQTT_BROKER, MQTT_TOPIC_RGB))    
    client.subscribe(MQTT_TOPIC_PHOTORESISTOR)
    print("Conectado a %s, en el topico %s"%(MQTT_BROKER, MQTT_TOPIC_PHOTORESISTOR))
    return client


# Función para conectar a la red WiFi
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


# Función para encender el LED rojo
def encender_led_rojo():
    led_rojo.on()

# Función para apagar el LED rojo
def apagar_led_rojo():
    led_rojo.off()

# Función para encender el LED verde
def encender_led_verde():
    led_verde.on()

# Función para apagar el LED verde
def apagar_led_verde():
    led_verde.off()

# Conectar a wifi
conectar_wifi()
# Subscripción a un broker mqtt
client = subscribir()

# Función principal para probar el sensor
def probar_sensor():
    ultima_publicacion = time.time()  # Variable para almacenar el tiempo de la última publicación
    while True:
        # Leer el valor del fotoresistor
        valor_fotoresistor = adc.read()
        print("Valor del fotoresistor:", valor_fotoresistor)
        client.publish(MQTT_TOPIC_PHOTORESISTOR, str(valor_fotoresistor))

        # Leer el valor analógico del sensor de fuego
        firesensor_analog = adc.read()
        client.publish(MQTT_TOPIC_LLAMA, str(firesensor_analog))

        # Si el valor del fotoresistor es bajo, enciende el LED verde y apaga el LED rojo
        if valor_fotoresistor < 3000:  # Puedes ajustar este umbral según tus necesidades
            encender_led_verde()
            apagar_led_rojo()
            client.publish(MQTT_TOPIC_RGB, b'0')
            client.publish(MQTT_TOPIC_RELAY, str(valor_fotoresistor))
        else:
            encender_led_rojo()
            apagar_led_verde()
            client.publish(MQTT_TOPIC_RGB, b'1')
            client.publish(MQTT_TOPIC_RELAY, str(1))
        
        # Verificar si han pasado 20 segundos desde la última publicación
        if time.time() - ultima_publicacion >= 10:
            # Publicar el mensaje MQTT
            if firesensor_analog > 3500:
                print("Fire detected", firesensor_analog)
            else:
                print("No fire detected", firesensor_analog)
            
            ultima_publicacion = time.time()  # Actualizar el tiempo de la última publicación
        
        time.sleep(5)  # Espera un breve tiempo antes de la próxima lectura para liberar el procesador
# Llama a la función principal para comenzar la prueba del sensor
if _name_ == "_main_":
    probar_sensor()