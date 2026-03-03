import pygame
import requests

url = "http://192.168.4.1/"

pygame.init()
pygame.joystick.init()

prev = "STOP"

joystick = pygame.joystick.Joystick(0)
joystick.init()

while True:
    pygame.event.pump()

    x = joystick.get_axis(2)
    y = joystick.get_axis(3)

    data = "STOP"

    if x > 0.3 and abs(y) < 0.3:
        data = "LEFT"
    elif x < -0.3 and abs(y) < 0.3:
        data = "RIGHT"
    elif abs(x) < 0.3 and y > 0.3:
        data = "BACKWARD"
    elif abs(x) < 0.3 and y < -0.3:
        data = "FORWARD"
    elif abs(x) < 0.3 and abs(y) < 0.3:
        data = "STOP"

    if prev != data:
        try:
            prev = data
            requests.get(url + data)
        except requests.exceptions.RequestException:
            print(f"Failed to send data: {data}")

    print(x, y, data)
