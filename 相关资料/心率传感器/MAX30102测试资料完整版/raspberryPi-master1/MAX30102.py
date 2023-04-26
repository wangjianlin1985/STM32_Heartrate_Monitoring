# -*-coding:utf-8-*-
import logging
from time import sleep

# import numpy as np
import smbus2 as smbus
import wiringpi as gpio
import smart_config

# register address- max30102
REG_INTR_STATUS_1 = 0x00
REG_INTR_STATUS_2 = 0x01

REG_INTR_ENABLE_1 = 0x02
REG_INTR_ENABLE_2 = 0x03

REG_FIFO_WR_PTR = 0x04
REG_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_FIFO_DATA = 0x07
REG_FIFO_CONFIG = 0x08

REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A
REG_LED1_PA = 0x0C

REG_LED2_PA = 0x0D
REG_PILOT_PA = 0x10
REG_MULTI_LED_CTRL1 = 0x11
REG_MULTI_LED_CTRL2 = 0x12

REG_TEMP_INTR = 0x1F
REG_TEMP_FRAC = 0x20
REG_TEMP_CONFIG = 0x21
REG_PROX_INT_THRESH = 0x30
REG_REV_ID = 0xFE
REG_PART_ID = 0xFF

# currently not used
MAX_BRIGHTNESS = 255


class MAX30102:
    # by default, this assumes that physical pin 7 (GPIO 4) is used as interrupt
    # by default, this assumes that the device is at 0x57 on channel 1
    def __init__(self, channel=1, address=0x57, gpio_pin=7):
        print("Channel: {0}, address: {1}".format(channel, address))
        self.address = address
        self.channel = channel
        self.bus = smbus.SMBus(self.channel)
        self.interrupt = gpio_pin

        # set gpio mode
        gpio.wiringPiSetup()  # 初始化wiringpi库
        gpio.pinMode(self.interrupt, 0)  # 设置针脚为输入状态

        self.reset()

        sleep(1)  # wait 1 sec

        # read & clear interrupt register (read 1 byte)
        reg_data = self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_1, 1)
        # print("[SETUP] reset complete with interrupt register0: {0}".format(reg_data))
        self.setup()
        # print("[SETUP] setup complete")

    def shutdown(self):
        """
        Shutdown the device.
        """
        self.bus.write_i2c_block_data(self.address, REG_MODE_CONFIG, [0x80])

    def reset(self):
        """
        Reset the device, this will clear all settings,
        so after running this, run setup() again.
        """
        self.bus.write_i2c_block_data(self.address, REG_MODE_CONFIG, [0x40])

    def setup(self, led_mode=0x03):
        """
        This will setup the device with the values written in sample Arduino code.
        """
        # INTR setting
        # 0xc0 : A_FULL_EN and PPG_RDY_EN = Interrupt will be triggered when
        # fifo almost full & new fifo data ready
        self.bus.write_i2c_block_data(self.address, REG_INTR_ENABLE_1, [0xc0])
        self.bus.write_i2c_block_data(self.address, REG_INTR_ENABLE_2, [0x00])

        # FIFO_WR_PTR[4:0]
        self.bus.write_i2c_block_data(self.address, REG_FIFO_WR_PTR, [0x00])
        # OVF_COUNTER[4:0]
        self.bus.write_i2c_block_data(self.address, REG_OVF_COUNTER, [0x00])
        # FIFO_RD_PTR[4:0]
        self.bus.write_i2c_block_data(self.address, REG_FIFO_RD_PTR, [0x00])

        # 0b 0100 1111
        # sample avg = 4, fifo rollover = false, fifo almost full = 17
        self.bus.write_i2c_block_data(self.address, REG_FIFO_CONFIG, [0x4f])

        # 0x02 for red-only, 0x03 for SpO2 mode, 0x07 multimode LED
        self.bus.write_i2c_block_data(self.address, REG_MODE_CONFIG, [led_mode])
        # 0b 0010 0111
        # SPO2_ADC range = 4096nA, SPO2 sample rate = 100Hz, LED pulse-width = 411uS
        self.bus.write_i2c_block_data(self.address, REG_SPO2_CONFIG, [0x27])

        # choose value for ~7mA for LED1
        self.bus.write_i2c_block_data(self.address, REG_LED1_PA, [0x24])
        # choose value for ~7mA for LED2
        self.bus.write_i2c_block_data(self.address, REG_LED2_PA, [0x24])
        # choose value fro ~25mA for Pilot LED
        self.bus.write_i2c_block_data(self.address, REG_PILOT_PA, [0x7f])

    # this won't validate the arguments!
    # use when changing the values from default
    def set_config(self, reg, value):
        self.bus.write_i2c_block_data(self.address, reg, value)

    def read_fifo(self):
        """
        This function will read the data register.
        """
        red_led = None
        ir_led = None

        # read 1 byte from registers (values are discarded)
        reg_INTR1 = self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_1, 1)
        reg_INTR2 = self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_2, 1)

        # read 6-byte data from the device
        d = self.bus.read_i2c_block_data(self.address, REG_FIFO_DATA, 6)

        # mask MSB [23:18]
        red_led = (d[3] << 16 | d[4] << 8 | d[5]) & 0x03FFFF
        ir_led = (d[0] << 16 | d[1] << 8 | d[2]) & 0x03FFFF

        return red_led, ir_led

    def read_sequential(self, amount=100):
        """
        This function will read the red-led and ir-led `amount` times.
        This works as blocking function.
        """
        red_buf = []
        ir_buf = []
        for i in range(amount):
            while gpio.digitalRead(self.interrupt) == 1:
                # wait for interrupt signal, which means the data is available
                # do nothing here
                pass

            red, ir = self.read_fifo()

            red_buf.append(red)
            ir_buf.append(ir)

        return red_buf, ir_buf

    # this assumes ir_data as np.array
    def calc_heart_rate(self, ir_data, sample_rate=25, ma_size=4):
        """
        By detecting  peaks of PPG cycle to calc hr
        """
        # sampling frequency * 4 (in algorithm.h)
        buffer_size = len(ir_data)

        # get dc mean
        # ir_mean = int(np.mean(ir_data))
        ir_mean = int(sum(ir_data) / float(len(ir_data)))
        # remove DC mean and inver signal
        # this lets peak detecter detect valley
        # x = -1 * (np.array(ir_data) - ir_mean)
        x = [-1 * (n - ir_mean) for n in ir_data]

        # 4 point moving average
        # x is np.array with int values, so automatically casted to int
        # for i in range(x.shape[0] - ma_size):
        #     x[i] = np.sum(x[i:i + ma_size]) / ma_size
        for i in range(len(x) - ma_size):
            x[i] = sum(x[i:i + ma_size]) / ma_size

        # calculate threshold
        # n_th = int(np.mean(x))
        n_th = int(sum(x) / float(len(x)))
        n_th = 30 if n_th < 30 else n_th  # min allowed
        n_th = 60 if n_th > 60 else n_th  # max allowed

        ir_valley_locs, n_peaks = self.find_peaks(x, buffer_size, n_th, 4, 15)
        # print(ir_valley_locs[:n_peaks], ",", end="")
        peak_interval_sum = 0
        if n_peaks >= 2:
            for i in range(1, n_peaks):
                peak_interval_sum += (ir_valley_locs[i] - ir_valley_locs[i - 1])
            peak_interval_sum = int(peak_interval_sum / (n_peaks - 1))
            hr = int(sample_rate * 60 / peak_interval_sum)
            hr_valid = True
        else:
            hr = -999  # unable to calculate because # of peaks are too small
            hr_valid = False

        return hr_valid, hr

    def find_peaks(self, x, size, min_height, min_dist, max_num):
        """
        (x, BUFFER_SIZE, n_th, 4, 15)
        Find at most MAX_NUM peaks above MIN_HEIGHT separated by at least MIN_DISTANCE
        """
        ir_valley_locs, n_peaks = self.find_peaks_above_min_height(x, size, min_height, max_num)
        ir_valley_locs, n_peaks = self.remove_close_peaks(n_peaks, ir_valley_locs, x, min_dist)

        n_peaks = min([n_peaks, max_num])

        return ir_valley_locs, n_peaks

    @staticmethod
    def find_peaks_above_min_height(x, size, min_height, max_num):
        """
        Find all peaks above MIN_HEIGHT
        """

        i = 0
        n_peaks = 0
        ir_valley_locs = []  # [0 for i in range(max_num)]
        while i < size - 1:
            if x[i] > min_height and x[i] > x[i - 1]:  # find the left edge of potential peaks
                n_width = 1
                # original condition i+n_width < size may cause IndexError
                # so I changed the condition to i+n_width < size - 1
                while i + n_width < size - 1 and x[i] == x[i + n_width]:  # find flat peaks
                    n_width += 1
                if x[i] > x[i + n_width] and n_peaks < max_num:  # find the right edge of peaks
                    # ir_valley_locs[n_peaks] = i
                    ir_valley_locs.append(i)
                    n_peaks += 1  # original uses post increment
                    i += n_width + 1
                else:
                    i += n_width
            else:
                i += 1

        return ir_valley_locs, n_peaks

    @staticmethod
    def remove_close_peaks(n_peaks, ir_valley_locs, x, min_dist):
        """
        Remove peaks separated by less than MIN_DISTANCE
        """

        # should be equal to maxim_sort_indices_descend
        # order peaks from large to small
        # should ignore index:0
        sorted_indices = sorted(ir_valley_locs, key=lambda index: x[index])
        sorted_indices.reverse()

        # this "for" loop expression does not check finish condition
        # for i in range(-1, n_peaks):
        i = -1
        while i < n_peaks:
            old_n_peaks = n_peaks
            n_peaks = i + 1
            # this "for" loop expression does not check finish condition
            # for j in (i + 1, old_n_peaks):
            j = i + 1
            while j < old_n_peaks:
                n_dist = (sorted_indices[j] - sorted_indices[i]) if i != -1 else (
                    sorted_indices[j] + 1)  # lag-zero peak of autocorr is at index -1
                if n_dist > min_dist or n_dist < -1 * min_dist:
                    sorted_indices[n_peaks] = sorted_indices[j]
                    n_peaks += 1  # original uses post increment
                j += 1
            i += 1

        sorted_indices[:n_peaks] = sorted(sorted_indices[:n_peaks])

        return sorted_indices, n_peaks


def calc_heart_rate(ir_data):
    """
    By detecting  peaks of PPG cycle to calc hr
    """
    # 25 samples per second (in algorithm.h)
    sample_freq = 25
    hr_valid = False
    hr = -999
    buffer_size = len(ir_data)
    ir_mean = sum(ir_data) / float(buffer_size)
    ir_data = [x - ir_mean for x in ir_data]
    ir_data = [1 if x > 0 else 0 for x in ir_data]
    positive_nums = sum([1 for x in ir_data if x > 0])
    if positive_nums > buffer_size * 2 / 3 or positive_nums < buffer_size / 3:
        return hr_valid, hr
    index_buffer = []
    for index in range(0, buffer_size - 1):
        if ir_data[index] == 1 and ir_data[index + 1] == 0:
            index_buffer.append(index)
    peak_nums = len(index_buffer) - 1
    if peak_nums <= 1:
        return hr_valid, hr
    else:
        peak_interval_sum = 0
        for index in range(0, peak_nums):
            peak_interval = index_buffer[index + 1] - index_buffer[index]
            peak_interval_sum = peak_interval_sum + peak_interval
        peak_interval_mean = peak_interval_sum / peak_nums
        hr = int(sample_freq * 60 / peak_interval_mean)
        hr_valid = True
        return hr_valid, hr

def calc_spo2(red_data,ir_data):

    spo2_valid = False
    spo2 = -999
    
    red_max = max(red_data)
    red_min = min(red_data)
    ir_max = max(ir_data)
    ir_min = min(ir_data)

    i_red_ac = red_max - red_min
    i_red_dc = (red_max + red_min)/2
    i_ir_ac = ir_max - ir_min
    i_ir_dc = (ir_max + ir_min)/2

    R = (i_red_ac)/(i_red_dc)/(i_ir_ac)/(i_ir_dc)
    spo2 = -45.060*R*R+ 30.354 *R + 94.845
    return spo2


def read_heart_rate(gpio_pin=7, n=100):
    gpio_pin = smart_config.phy2wpi[gpio_pin]
    max30102 = MAX30102(gpio_pin=gpio_pin)
    while True:
        logging.info('read from max30102 once')
        red_buf, ir_buf = max30102.read_sequential(amount=n)
        spo2 = calc_spo2(red_buf,ir_buf)
        hr_valid, hr = max30102.calc_heart_rate(ir_buf)
        logging.info(hr_valid)
        logging.info(hr)
        logging.info(spo2)
        if hr_valid:
            logging.info(ir_buf)
            with open('hrdump.log', 'a') as output:
                line = str(hr) + ' [' + ','.join([str(x) for x in ir_buf]) + ']\n'
                output.write(line)
            max30102.shutdown()
            return hr
        max30102.reset()
        max30102.setup(led_mode=0x03)


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(filename)s[line:%(lineno)d] - %(funcName)s : %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    hr = read_heart_rate(7, 100)
    logging.info('test once')
    hr = read_heart_rate(7, 100)
    logging.info('test once')


if __name__ == '__main__':
    main()
