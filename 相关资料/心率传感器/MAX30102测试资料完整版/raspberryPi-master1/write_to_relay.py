# coding=utf-8
import sys

import wiringpi as gpio
import smart_config


def set_value(gpio_pin: int, value: int):
    gpio_pin = smart_config.phy2wpi[gpio_pin]
    gpio.wiringPiSetup()  # 初始化wiringpi库
    gpio.pinMode(gpio_pin, 1)  # 设置针脚为输出状态
    gpio.digitalWrite(gpio_pin, value)  # 输出电平0,1


def blink(gpio_pin: int, delay: int):
    for i in range(10):
        print(i)
        set_value(gpio_pin, i % 2)
        gpio.delay(delay)


def main(gpio_pin=2):
    if len(sys.argv) > 1:
        gpio_pin = int(sys.argv[1])
    blink(gpio_pin, 500)


if __name__ == '__main__':
    main()
