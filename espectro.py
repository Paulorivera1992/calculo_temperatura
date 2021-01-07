from seabreeze.spectrometers import Spectrometer
import numpy as np
import matplotlib.pyplot as plt

spec = Spectrometer.from_first_available()
spec.integration_time_micros(20000)


for i in range(1):
  wavelengths = spec.wavelengths() #lee longitudes de onda wavelengths in (nm)
  intensities = spec.intensities() #lee intensidades measured intensity array in (a.u.)

  f = open ('longitud'+str(i)+'.txt','wb')
  np.savetxt(f, np.array(wavelengths))
  f.close()
  f = open ('intensidad'+str(i)+'.txt','wb')
  np.savetxt(f, intensities)
  f.close()

  plt.plot(wavelengths,intensities)
  plt.xlabel('wavelengths')
  plt.ylabel('intensities')
  plt.title('Lab DLS')
plt.show()