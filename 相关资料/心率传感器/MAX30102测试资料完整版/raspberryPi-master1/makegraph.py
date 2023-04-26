# -*-coding:utf-8-*-

import matplotlib.pyplot as plt

# load log data
# red = []
# with open("./red.log", "r") as f:
#     for r in f:
#         red.append(int(r))
import numpy as np


def calc_heart_rate_0(ir_data):
    """
    By detecting  peaks of PPG cycle to calc hr
    """
    # 25 samples per second (in algorithm.h)
    SAMPLE_FREQ = 25
    # taking moving average of 4 samples when calculating HR
    # in algorithm.h, "DONOT CHANGE" comment is attached
    MA_SIZE = 4
    # sampling frequency * 4 (in algorithm.h)
    BUFFER_SIZE = 100

    # get dc mean
    ir_mean = int(np.mean(ir_data))

    # remove DC mean and inver signal
    # this lets peak detecter detect valley
    x = -1 * (np.array(ir_data) - ir_mean)

    # 4 point moving average
    # x is np.array with int values, so automatically casted to int
    for i in range(x.shape[0] - MA_SIZE):
        x[i] = np.sum(x[i:i + MA_SIZE]) / MA_SIZE

    # calculate threshold
    n_th = int(np.mean(x))
    n_th = 30 if n_th < 30 else n_th  # min allowed
    n_th = 60 if n_th > 60 else n_th  # max allowed
    # print(x)
    ir_valley_locs, n_peaks = find_peaks(x, BUFFER_SIZE, n_th, 4, 15)
    print(ir_valley_locs[:n_peaks])
    peak_interval_sum = 0
    if n_peaks >= 2:
        for i in range(1, n_peaks):
            peak_interval_sum += (ir_valley_locs[i] - ir_valley_locs[i - 1])
        print(peak_interval_sum)
        print(n_peaks - 1)
        peak_interval_sum = int(peak_interval_sum / (n_peaks - 1))
        print(peak_interval_sum)
        hr = int(SAMPLE_FREQ * 60 / peak_interval_sum)
        hr_valid = True
    else:
        hr = -999  # unable to calculate because # of peaks are too small
        hr_valid = False

    return hr_valid, hr


def find_peaks(x, size, min_height, min_dist, max_num):
    """
    (x, BUFFER_SIZE, n_th, 4, 15)
    Find at most MAX_NUM peaks above MIN_HEIGHT separated by at least MIN_DISTANCE
    """
    ir_valley_locs, n_peaks = find_peaks_above_min_height(x, size, min_height, max_num)
    ir_valley_locs, n_peaks = remove_close_peaks(n_peaks, ir_valley_locs, x, min_dist)

    n_peaks = min([n_peaks, max_num])

    return ir_valley_locs, n_peaks


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
    ma_size = 4
    hr_valid = False
    hr = -999
    buffer_size = len(ir_data)
    for i in range(buffer_size - 4):
        ir_data[i] = sum(ir_data[i:i + ma_size]) / ma_size
    ir_data = ir_data[0: buffer_size - ma_size]
    buffer_size = len(ir_data)
    ir_mean = int(sum(ir_data) / buffer_size)
    ir_data = [x - ir_mean for x in ir_data]
    index_buffer = []
    for index in range(1, buffer_size - 1):
        if ir_data[index] > ir_data[index + 1] and ir_data[index] >= ir_data[index - 1]:
            index_buffer.append(index)
    print(index_buffer)
    index_interval_buffer = []
    for index in range(0, len(index_buffer) - 1):
        index_interval_buffer.append(index_buffer[index + 1] - index_buffer[index])
    print(index_interval_buffer)
    index_buffer, n_peaks = remove_close_peaks(len(index_buffer), index_buffer, ir_data, 4)
    index_buffer = index_buffer[:n_peaks]
    print(index_buffer)
    index_interval_buffer = []
    for index in range(0, len(index_buffer) - 1):
        index_interval_buffer.append(index_buffer[index + 1] - index_buffer[index])
    print(index_interval_buffer)
    if n_peaks <= 1:
        return hr_valid, hr
    hr_valid = True
    print((index_buffer[-1] - index_buffer[0]))
    print(len(index_buffer) - 1)
    peak_interval_mean = (index_buffer[-1] - index_buffer[0]) / (len(index_buffer) - 1)
    print(peak_interval_mean)
    hr = int(sample_freq * 60 / peak_interval_mean)
    return hr_valid, hr
    # print(index_buffer)
    # print(n_peaks)
    # print((index_buffer[-1] - index_buffer[0]) / len(index_buffer))
    # peak_nums = len(index_buffer) - 1
    # if peak_nums <= 1:
    #     return hr_valid, hr
    # else:
    #     peak_interval_buffer = []
    #     for index in range(0, peak_nums):
    #         peak_interval_buffer.append(index_buffer[index + 1] - index_buffer[index])
    #     print(peak_interval_buffer)
    #     peak_interval_dict = {}
    #     for x in peak_interval_buffer:
    #         c = 0
    #         if x in peak_interval_dict:
    #             c = peak_interval_dict[x]
    #         peak_interval_dict[x] = c + 1
    #     max_key = 0
    #     max_c = 0
    #     for key in peak_interval_dict:
    #         if peak_interval_dict[key] > max_c:
    #             max_c = peak_interval_dict[key]
    #             max_key = key
    #     print(peak_interval_dict)
    #     peak_interval_mean = max_key
    #     hr = int(sample_freq * 60 / peak_interval_mean)
    #     hr_valid = True
    #     return hr_valid, hr


ir2 = [94225, 94225, 94225, 79715, 94178, 94429, 94273, 94328, 94218, 94297, 94215, 94215, 94051, 94264, 93817, 94270,
       94270, 93622, 94227, 94227, 93627, 94197, 94197, 94197, 93662, 94122, 94122, 94122, 93785, 94142, 94142, 93827,
       94172, 94172, 94172, 94172, 93794, 94202, 94202, 94202, 94202, 93838, 94302, 94302, 94302, 94302, 93752, 94307,
       94307, 94307, 93687, 94283, 94283, 94283, 94283, 93792, 94263, 94263, 94263, 94263, 93722, 94220, 94220, 94220,
       94220, 93473, 94246, 94246, 94246, 94246, 92800, 94303, 94303, 94303, 92047, 94450, 94450, 94450, 90904, 94720,
       94720, 94720, 90863, 94966, 94966, 94966, 94966, 91559, 95166, 95166, 95166, 95166, 92257, 95364, 95364, 95364,
       95364, 92555, 95541, 95541]
ir3 = [81105, 81105, 80892, 98740, 98740, 98740, 98740, 98624, 98731, 98731, 98731, 98731, 98582, 98843, 98843, 98843,
       98843, 98530, 98888, 98888, 98888, 98888, 98531, 98944, 98944, 98944, 98944, 98674, 99460, 99460, 99460, 99460,
       98778, 99518, 99518, 99518, 99518, 98855, 98989, 98989, 98989, 98989, 98989, 99084, 99084, 99084, 99084, 99195,
       99195, 99195, 99195, 99284, 99284, 99284, 99284, 99353, 99353, 99353, 99105, 99424, 99424, 99424, 99168, 99509,
       99509, 99509, 99200, 99532, 99532, 99532, 99262, 99220, 99220, 99220, 99337, 98645, 98645, 98645, 99387, 98428,
       98428, 98428, 99403, 98445, 98445, 98445, 99072, 98448, 98448, 98448, 98448, 98571, 118315, 118315, 118315,
       118315, 98373, 151157, 151157, 151157]
ir4 = [72589, 75133, 79393, 80341, 81733, 84735, 89001, 93300, 26833, 95496, 13235, 13235, 13235, 13235, 97015, 6791,
       6791, 6791, 6791, 97979, 3701, 3701, 3701, 3701, 3701, 3701, 97824, 2396, 2396, 2396, 2396, 2396, 2396, 2396,
       2396, 98485, 1877, 1877, 1877, 1877, 1877, 1877, 99090, 1699, 1699, 1699, 1699, 1699, 99097, 1670, 1670, 1670,
       1670, 99419, 1598, 1598, 1598, 1598, 99873, 1549, 1549, 1549, 100159, 1536, 1536, 1536, 1536, 100499, 1486, 1486,
       1486, 1486, 100886, 1425, 1425, 1425, 101694, 70661, 70661, 70661, 102214, 70656, 70656, 70656, 103204, 70656,
       70656, 70656, 70656, 70656, 70656, 104001, 70682, 70682, 70682, 70682, 70682, 104263, 70693, 70693, 70693, 70693,
       104543, 70717, 70717, 70717, 70717, 70717, 104880, 70713, 70713, 70713, 70713, 70713, 70713, 105093, 70737,
       70737, 70737, 70737, 70737, 105403, 70759, 70759, 70759, 70759, 70759, 105389, 70748, 70748, 70748, 70748, 70748,
       70748, 104512, 70685, 70685, 70685, 70685, 103642, 72589, 103353, 75133, 75133, 75133, 103109, 79393, 79393,
       103231, 80341, 80341, 103355, 81733, 81733, 103407, 84735, 84735, 84735, 103368, 89001, 89001, 89001, 103290,
       93300, 93300, 93300, 103463, 95496, 95496, 95496, 103727, 97015, 97015, 97015, 103694, 97979, 97979, 97979,
       103520, 97824, 97824, 97824, 103060, 98485, 98485, 102151, 99090, 99090, 101266, 99097, 99097, 99097, 100975,
       99419, 99419, 99419, 101024, 99873, 99873, 99873]
ir5 = [103353, 103353, 103353, 79761, 103109, 103109, 103109, 94561, 103231, 103231, 103231, 94584, 103355, 103355,
       103355, 94399, 103407, 103407, 103407, 103407, 93887, 103368, 103368, 103368, 103368, 93320, 103290, 103290,
       103290, 103290, 93004, 103463, 103463, 103463, 103463, 103463, 92760, 103727, 103727, 103727, 103727, 103727,
       92639, 103694, 103694, 103694, 103694, 92482, 103520, 103520, 103520, 103520, 103520, 92185, 103060, 103060,
       103060, 103060, 91924, 102151, 102151, 102151, 102151, 91834, 101266, 101266, 101266, 101266, 91779, 100975,
       100975, 100975, 100975, 91728, 101024, 101024, 101024, 101024, 91611, 101080, 101080, 101080, 101080, 101080,
       91516, 100159, 100159, 100159, 100159, 100159, 91551, 100499, 100499, 100499, 100499, 91530, 100886, 100886,
       100886, 100886, 100886, 91396, 101694, 101694, 101694, 101694, 91357, 102214, 102214, 102214, 102214, 91444,
       103204, 103204, 103204, 103204, 91456, 104001, 104001, 104001, 104001, 91422, 104263, 104263, 104263, 104263,
       91436, 104543, 104543, 104543, 104543, 91395, 104880, 104880, 104880, 104880, 91366, 105093, 105093, 105093,
       105093, 105093, 105093, 91365, 105403, 105403, 105403, 105403, 105403, 91282, 105389, 105389, 105389, 105389,
       105389, 91176, 104512, 104512, 104512, 104512, 104512, 91061, 103642, 103642, 103642, 103642, 103642, 90694,
       79761, 79761, 79761, 79761, 79761, 90294, 94561, 94561, 94561, 94561, 89979, 94584, 94584, 94584, 94584, 89858,
       94399, 94399, 94399, 94399, 94399, 89701, 93887, 93887, 93887, 93887, 89470, 93320, 93320, 93320, 93320, 89207]
print(calc_heart_rate(ir5[0:200])[1] / 4)
print('#########################')
print(calc_heart_rate(ir5[0:100])[1] / 4)
print('#########################')
print(calc_heart_rate_0(ir5[0:100])[1] / 4)
# with open("./hrdump.log", "r") as f:
#     for r in f:
#         ir.append(int(r))

# x-axis values
# l = [ir1, ir2, ir3, ir4, ir5]
# for ir in l:
#        y = ir
#        x = [x for x in range(0, len(y))]
#        plt.figure()
#        plt.plot(x, y)
# y = ir4
# x = [x for x in range(0, len(y))]
# # sum_y = 0.0
# # for yi in y:
# #     sum_y += yi
# # sum_y /= len(y)
# # print(sum_y)
# x = x[0:100]
# y = y[0:100]
# # y = [yi - sum_y for yi in y]
# plt.figure()
# plt.plot(x, y)
# plt.xticks(range(len(x)))
# plt.show()
# fig = plt.figure()
# ax = fig.add_subplot(1, 1, 1)
# ax.plot(x, y)
# plt.xlabel('x')
# plt.ylabel('y')
# plt.legend(['line1','line2'])
# plt.show()
