import datetime
import random
import time
import logging
from optparse import OptionParser

import DHT11
import MAX30102
import smart_config
import write_to_relay
import matplotlib.pyplot as plt


class Record:
    loop = 0
    last_cmd = smart_config.Status.OPEN
    last_status = smart_config.Status.UNKNOWN


def get_args():
    parser = OptionParser()
    parser.add_option(
        '--dht11',
        action='store',
        dest='dht11',
        type='str',
        default='37',
        help='dht11 gpio wiringpi pins'
    )
    parser.add_option(
        '--max30102',
        action='store',
        dest='max30102',
        type='str',
        default='7',
        help='max30102 gpio wiringpi pin'
    )
    parser.add_option(
        '--relay',
        action='store',
        dest='relay',
        type='str',
        default='12',
        help='relay gpio wiringpi pin'
    )
    parser.add_option(
        '--loop',
        action='store',
        dest='loop',
        type='int',
        default=0,
        help='run the controller loop times, 0 means never stop'
    )
    parser.add_option(
        '--model',
        action='store',
        dest='model',
        type='str',
        default='physical',
        help='gpio pin model, physical or wiringpi'
    )
    parser.add_option(
        '--debug',
        action='store',
        dest='debug',
        type='int',
        default=0,
        help=' print all log'
    )
    parser.add_option(
        '--test',
        action='store',
        dest='test',
        type='int',
        default=0,
        help=' just blink the relay every test second pass'
    )
    (opt, args) = parser.parse_args()
    if opt.model == 'wiringpi':
        for key in smart_config.phy2wpi:
            smart_config.phy2wpi[key] = key
    return opt


def test_case(opt):
    relay_gpio_pin = int(opt.relay)
    test = int(opt.test)
    write_to_relay.blink(relay_gpio_pin, test)
    return


def search_status(humidity, temperature, heart_rate):
    status = smart_config.Status.UNKNOWN
    if humidity < smart_config.Humidity.down_threshold:
        status = smart_config.Status.COLD
    elif humidity > smart_config.Humidity.up_threshold:
        if heart_rate > smart_config.HeartRate.up_threshold:
            status = smart_config.Status.SPORT
        elif heart_rate < smart_config.HeartRate.down_threshold:
            status = smart_config.Status.HOT
    else:
        status = smart_config.Status.UNKNOWN
    # 检查逻辑，如果传感器数据不合情理，则修改状态
    if status != smart_config.Status.UNKNOWN:
        if status == smart_config.Status.COLD:
            if heart_rate > smart_config.HeartRate.up_threshold:
                # 湿度低于阈值，但是心率很高，也就是人体一直在运动，但是不出汗，湿度很低，不合理
                status = smart_config.Status.UNKNOWN
            if temperature > smart_config.Temperature.up_threshold:
                # 湿度低于阈值，但是温度很高，也就是人体一直在发热，但是不出汗，不合理
                status = smart_config.Status.UNKNOWN
    return status


def init(opt):
    plt.ion()
    plt.figure(1)
    last_cmd = smart_config.Status.CLOSE
    relay_gpio_pin = int(opt.relay)
    write_to_relay.set_value(relay_gpio_pin, last_cmd)
    record = Record()
    record.last_status = smart_config.Status.UNKNOWN
    record.last_cmd = last_cmd
    record.loop = int(opt.loop)
    smart_config.debug = (int(opt.debug) != 0)
    return record


def set_status(record: Record, status, relay_gpio_pin, cmd):
    write_to_relay.set_value(relay_gpio_pin, cmd)
    record.last_cmd = cmd
    record.last_status = status
    if record.loop > 1:
        record.loop -= 1
    relay_status = 'close'
    if cmd == smart_config.Status.OPEN:
        relay_status = 'open'
    logging.info('switch relay status to ' + relay_status)
    people_status = 'unknown'
    if status == smart_config.Status.COLD:
        people_status = 'cold'
    if status == smart_config.Status.HOT:
        people_status = 'hot'
    if status == smart_config.Status.SPORT:
        people_status = 'sport'
    logging.info('people current status is ' + people_status)
    return record


def show(x_src, y_src):
    plt.clf()
    (y1_src, y2_src, y3_src) = y_src
    x = x_src[len(x_src) - 10:]
    y1 = y1_src[len(y1_src) - 10:]
    y2 = y2_src[len(y2_src) - 10:]
    y3 = y3_src[len(y3_src) - 10:]
    # plt.xlim、plt.ylim 设置横纵坐标轴范围
    # plt.xlabel、plt.ylabel 设置坐标轴名称
    # plt.xticks、plt.yticks 设置坐标轴刻度
    #  axes.set_* 同上
    plt.subplot(411)
    plt.plot(x, y1, color='r')
    plt.xticks(range(x[0], x[-1] + 1, 1))
    plt.yticks(range(0, 45, 5))
    plt.ylabel('temperature')
    plt.subplot(412)
    plt.plot(x, y2, color='y')
    plt.xticks(range(x[0], x[-1] + 1, 1))
    plt.yticks(range(0, 120, 10))
    plt.ylabel('humidity')
    plt.subplot(413)
    plt.plot(x, y3, color='g')
    plt.xticks(range(x[0], x[-1] + 1, 1))
    plt.yticks(range(0, 220, 20))
    plt.ylabel('heart_rate')
    plt.subplot(414)
    plt.axis('off')
    plt.text(0, 0, "temperature:" + str(y1[-1]))
    plt.text(0.35, 0, "humidity:" + str(y2[-1]))
    plt.text(0.7, 0, "heart_rate:" + str(y3[-1]))
    plt.pause(0.5)


def run(opt):
    dht11_gpio_pins = opt.dht11
    dht11_gpio_pins = dht11_gpio_pins.split(',')
    dht11_gpio_pins = [int(x) for x in dht11_gpio_pins]
    max30102_gpio_pin = int(opt.max30102)
    relay_gpio_pin = int(opt.relay)
    record = init(opt)
    time_index = 10
    x = [i for i in range(-9, 0)]
    y1 = [25] * len(x)
    y2 = [20] * len(x)
    y3 = [50] * len(x)
    while True:
        global_dht11_index = random.randint(0, 1)
        humidity, temperature = DHT11.read_temperature_and_humidity(dht11_gpio_pins, global_dht11_index)
        heart_rate = MAX30102.read_heart_rate(max30102_gpio_pin, 100)
        status = search_status(humidity, temperature, heart_rate)
        x.append(time_index)
        y1.append(temperature)
        y2.append(humidity)
        y3.append(heart_rate)
        if len(x) > 200:
            x = x[len(x) - 100:]
            y1 = y1[len(y1) - 100:]
            y2 = y2[len(y2) - 100:]
            y3 = y3[len(y3) - 100:]
        y = (y1, y2, y3)
        show(x, y)
        time_index += 1
        if status == smart_config.Status.UNKNOWN:
            continue
        if record.last_cmd == smart_config.Status.CLOSE and status != smart_config.Status.COLD:
            record = set_status(record, status, relay_gpio_pin, smart_config.Status.OPEN)
        elif record.last_cmd == smart_config.Status.OPEN and status == smart_config.Status.COLD:
            record = set_status(record, status, relay_gpio_pin, smart_config.Status.CLOSE)
        if record.loop == 1:
            break
        time.sleep(2)


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(filename)s[line:%(lineno)d] - %(funcName)s : %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    opt = get_args()
    test = int(opt.test)
    if test != 0:
        test_case(opt)
    else:
        run(opt)


if __name__ == '__main__':
    main()
