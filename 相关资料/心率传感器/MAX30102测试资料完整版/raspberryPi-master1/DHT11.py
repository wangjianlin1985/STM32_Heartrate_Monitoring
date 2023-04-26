# coding=utf-8
import logging
import sys
import time

import wiringpi as gpio
import smart_config


class DHT11:
    def __init__(self, gpio_pin=25):
        self.gpio_pin = gpio_pin
        self.wait_micros_second = 10000
        self.end_micros_second = 500

    def read_signal(self):
        data_time_list = []  # 存放每个数据位的时间
        data_bit_list = []  # 存放数据位
        gpio.wiringPiSetup()  # 初始化wiringpi库
        gpio.pinMode(self.gpio_pin, 1)  # 设置针脚为输出状态
        gpio.digitalWrite(self.gpio_pin, 1)  # 输出高电平10ms
        gpio.delay(10)
        gpio.digitalWrite(self.gpio_pin, 0)  # 拉低25ms开始指令
        gpio.delay(25)
        gpio.digitalWrite(self.gpio_pin, 1)  # 抬高20us
        gpio.delayMicroseconds(20)
        gpio.pinMode(self.gpio_pin, 0)  # 设针脚为输入状态
        tc = gpio.micros()
        while gpio.digitalRead(self.gpio_pin) == 1:
            # 等待DHT11拉低管脚
            if gpio.micros() - tc > self.wait_micros_second:  # 如果超过 10ms 就报错
                return data_bit_list

        for i in range(45):  # 测试每个数据周期的时间（包括40bit数据加一个发送开始标志
            tc = gpio.micros()  # 记下当前us数（从初始化开始算起，必要时重新初始化）
            '''
            一个数据周期，包括一个低电平，一个高电平，从DHT11第一次拉低信号线开始
            到DHT11发送最后一个50us的低电平结束（然后被拉高，一直维持高电平，所以
            最后的完成标志是一直为高，超过500ms）
            '''
            while gpio.digitalRead(self.gpio_pin) == 0:
                if gpio.micros() - tc > self.end_micros_second:  # 如果超过 500us 就报错
                    return data_bit_list
            while gpio.digitalRead(self.gpio_pin) == 1:
                if gpio.micros() - tc > self.end_micros_second:  # 如果超过500us就结束了
                    break
            if gpio.micros() - tc > self.end_micros_second:  # 跳出整个循环
                break
            data_time_list.append(gpio.micros() - tc)  # 记录每个周期时间的us数，存到tl这个列表
        logging.debug(data_time_list)
        logging.debug('len of signal is ' + str(len(data_time_list)))
        if len(data_time_list) == 41:
            data_time_list = data_time_list[1:]
        for i in data_time_list:
            if i > 100:  # 若数据位为1，时间为50us低电平+70us高电平=120us
                data_bit_list.append(1)
            else:
                data_bit_list.append(0)  # 若数据位为0，时间为50us低电平+25us高电平=75us
                # 这里取大于100us就为1
        return data_bit_list

    def sample_signal_and_visualize(self):
        humidity_int = 0
        humidity_fraction = 0.0
        temperature_int = 0
        temperature_fraction = 0.0
        check_sum = 0
        result = self.read_signal()
        logging.debug('len of signal is ' + str(len(result)))
        check_right = False
        if len(result) == 40:
            for index in range(8):
                # 计算每一位的状态，每个字8位，以此为湿度整数，湿度小数，温度整数，温度小数，校验和
                humidity_int *= 2
                humidity_int += result[index]
                humidity_fraction *= 2
                humidity_fraction += result[index + 8]
                temperature_int *= 2
                temperature_int += result[index + 16]
                temperature_fraction *= 2
                temperature_fraction += result[index + 24]
                check_sum *= 2
                check_sum += result[index + 32]

            logging.debug('湿度:' + str(humidity_int) + '.' + str(int(humidity_fraction)))
            logging.debug('温度:' + str(temperature_int) + '.' + str(int(temperature_fraction)))
            if ((humidity_int + int(humidity_fraction) + temperature_int + int(
                    temperature_fraction)) % 256) == check_sum \
                    and check_sum != 0:
                check_right = True
            else:
                logging.warning("Read Sucess,But checksum error!")
        else:
            logging.warning("Read failer!")
        return check_right, humidity_int, humidity_fraction, temperature_int, temperature_fraction


def read_temperature_and_humidity(gpio_pins: list, global_dht11_index: int):
    gpio_pins = [smart_config.phy2wpi[x] for x in gpio_pins]
    numbers_of_dht11 = len(gpio_pins)
    while True:
        dht11_obj = DHT11(gpio_pins[global_dht11_index % numbers_of_dht11])
        check_right, humidity_int, humidity_fraction, temperature_int, temperature_fraction = \
            dht11_obj.sample_signal_and_visualize()
        if check_right:
            break
        gpio.delay(500)
        global_dht11_index += 1
    while humidity_fraction >= 1:
        humidity_fraction /= 10.0
    while temperature_fraction >= 1:
        temperature_fraction /= 10.0
    humidity = float(humidity_int + humidity_fraction)
    temperature = float(temperature_int + temperature_fraction)
    return humidity, temperature


def main(gpio_pins='37,23'):
    if len(sys.argv) > 1:
        gpio_pins = sys.argv[1]
    # time_sum = 0
    gpio_pins = gpio_pins.split(',')
    gpio_pins = [int(x) for x in gpio_pins]
    print(gpio_pins)
    for i in range(0, 10):
        humidity, temperature = read_temperature_and_humidity(gpio_pins, 0)
        print('湿度:' + str(humidity))
        print('温度:' + str(temperature))
        # time_sum += count
        time.sleep(1)
    # print(time_sum)
    # print(time_sum / 100.0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(filename)s[line:%(lineno)d] - %(funcName)s : %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    main()
