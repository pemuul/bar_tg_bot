import sys
import time

print('элемент 1')
print('элемент 2')
print('элемент 3')

# Подождите некоторое время, чтобы "элемент 1" был виден в консоли
time.sleep(2)

# Воспользуйтесь символом возврата каретки (CR), чтобы вернуться в начало строки
sys.stdout.write('\r')

# Затем выведите пробелы, чтобы перезаписать "элемент 1"
sys.stdout.write(' ' * len('элемент 1'))

# Очистите буфер вывода
sys.stdout.flush()

# Вернемся в начало следующей строки
sys.stdout.write('\n')
sys.stdout.flush()