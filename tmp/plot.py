from scipy import stats
import numpy as np
import matplotlib.pyplot as plt

file = open('temp_measurements2', 'r')
lines = file.readlines()

measurements = [[], []]

for line in lines:
    l = line.split(" ")
    measurements[0].append(float(l[1]))
    measurements[1].append(float(l[0]))

print(measurements)

fit = stats.linregress(np.array(measurements[0]), np.array(measurements[1]))

#print(fit)

plt.plot(measurements[0], measurements[1], label='raw data', ls='', marker='.')
plt.plot(measurements[0], np.log10(np.array(measurements[0])) * 950 + 1880, 'r', label='yololine')
plt.plot(measurements[0], np.log(np.array(measurements[0])) * 385 + 2000, 'b', label='yololine')
#plt.plot(measurements[0], fit.intercept + fit.slope*np.array(measurements[0]), 'r', label='fitted line')
#plt.semilogx()
plt.ylabel('temps')
plt.legend()
plt.show()
