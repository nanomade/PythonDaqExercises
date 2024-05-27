import time

import usbtmc
import numpy as np
import matplotlib.pyplot as plt

class TektronixTDS():
    # Docs: https://mmrc.caltech.edu/Oscilliscope/TDS200%20Programer.pdf
    #
    # Currently requires to run the venv'ed python suid root.
    # Alternatively follow these udev-instructions:
    # http://alexforencich.com/wiki/en/python-usbtmc/readme
    #
    # pyvisa-based alternative backend
    # import pyvisa
    # visaRsrcAddr = "USB0::1689::934::C020128::0::INSTR"
    # scope = rm.open_resource(visaRsrcAddr)
    # :ACQuire?
    # ACQuire:MODe { SAMple | PEAKdetect | AVErage }
    # ACQuire:NUMAVg <NR1>

    def __init__(self):
        self.instr = usbtmc.Instrument(0x699, 0x3a6)

        # Ascii format also exists but this is almost 10 times faster
        self.instr.write('DATa:ENCdg RIBinary')
        # self.v_offset = None 
        self.sample_interval = self.v_scale = self.v_offset = None
        self.update_scale_info()
        
    def update_scale_info(self):
        """
        Ask the instrument for the screen parameters.
        This is a primitive implementation where each parameter is read
        one-by-one. We could also get all information in one go.
        """
        self.sample_interval = float(self.instr.ask('WFMPre:XINcr?'))
        # These will be a lists, since each channel can be different
        self.v_scale = float(self.instr.ask('WFMPre:YMUlt?'))
        self.v_offset = float(self.instr.ask('WFMPre:YOFf?')) * self.v_scale
        return self.sample_interval, self.v_scale, self.v_offset

    def get_waveform(self):
        """
        Retrive a full waveform. X-axis is generated from number of
        samples and self.sample_interval. Trigger point is currently
        not registred.
        """
        # Use ask_raw since the result is not valid unicode
        y_data_raw = self.instr.ask_raw(b'CURVe?')
        y_data = np.frombuffer(y_data_raw, dtype=np.int8)
        y_data = y_data[6:-1]  # Six first and last byte is invalid
        y_data = y_data * self.v_scale + self.v_offset
        x_data = np.arange(0, len(y_data)) * self.sample_interval
        return x_data, y_data

        
    
if __name__ == '__main__':
    import matplotlib.animation as animation
    tds = TektronixTDS()

    def calculate_fft(x, y, subtract_dc=True):
        sr = 1/(x[1] - x[0])  # Sample rate
        n = np.arange(len(y))
        T = len(y) / sr
        freq = n / T 

        mean_y = 0
        if subtract_dc:
            mean_y = sum(y) / len(y)
        fft = abs(np.fft.fft(y - mean_y))
        # fft = abs(np.fft.rfft(y - mean_y))[1:]
        return freq[1:], fft[1:]

    def animate(i):
        tds.update_scale_info()

        x_data, y_data = tds.get_waveform()
        freq, fft = calculate_fft(x_data, y_data)

        line_data.set_xdata(x_data)
        line_data.set_ydata(y_data)

        line_fft.set_xdata(freq)
        line_fft.set_ydata(fft)

        axis.set_xlim(0, max(x_data))
        axis2.set_xlim(0, max(freq)/2)
        line = [line_data, line_fft]
        # line = line_data
        #return line,
        return line

    fig = plt.figure()
    axis = fig.add_subplot(2, 1, 1)
    axis2 = fig.add_subplot(2, 1, 2)

    x_data, y_data = tds.get_waveform()
    freq, fft = calculate_fft(x_data, y_data)

    line_data, = axis.plot(x_data, y_data, 'r-')   
    line_fft, = axis2.plot(freq, fft, 'r-')

    axis2.set_yscale('log')
    axis2.set_ylim(0.1, 1e5)

    # If blit=True, the tickmarks is not automatically updated...
    ani = animation.FuncAnimation(
        fig, animate, interval=2, blit=False, save_count=1
    )
   
    plt.show()
