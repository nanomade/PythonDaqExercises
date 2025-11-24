import time
import csv

import matplotlib.pyplot as plt


class Plotter:
    def __init__(self):
        self._clear_data()
        self.running = True

    def _clear_data(self):
        self.data = {
            'time': [],
            'gate': [],
            'dmm': [],
        }
        return

    @staticmethod
    def _conductivity(dmm_data):
        conductivity = [0] * len(dmm_data)
        for i in range(0, len(dmm_data)):
            conductivity[i] = 1 / dmm_data[i]
        return conductivity

    def on_close(self, event):
        self.running = False

    def update_spectrum(self):
        self.read_data()

        min_gate = min(self.data['gate'])
        max_gate = max(self.data['gate'])
        min_dmm = min(self.data['dmm'])
        max_dmm = max(self.data['dmm'])

        self.fig.canvas.flush_events()
        self.gate_dmm_plot.set_xdata([self.data['gate']])
        self.gate_dmm_plot.set_ydata([self.data['dmm']])
        self.ax1.set_xlim([min_gate, max_gate])
        self.ax1.set_ylim([min_dmm, max_dmm])

        conductivity = self._conductivity(self.data['dmm'])
        min_con = min(conductivity)
        max_con = max(conductivity)
        self.gate_conductivity_plot.set_xdata([self.data['gate']])
        self.gate_conductivity_plot.set_ydata(conductivity)
        self.ax2.set_xlim([min_gate, max_gate])
        self.ax2.set_ylim([min_con, max_con])

        self.dmm_plot.set_xdata([self.data['time']])
        self.dmm_plot.set_ydata([self.data['dmm']])
        self.gate_plot.set_xdata([self.data['time']])
        self.gate_plot.set_ydata([self.data['gate']])

        self.ax3.set_xlim([0, self.data['time'][-1] + 2])
        self.ax3.set_ylim([min_dmm, max_dmm])
        self.ax3_2.set_ylim([min_gate, max_gate])

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.01)

    def plot_spectrum(self):
        plt.ion()
        self.fig = plt.figure()

        # DMM plot
        self.ax1 = self.fig.add_subplot(3, 1, 1)
        (self.gate_dmm_plot,) = self.ax1.plot(
            self.data['gate'], self.data['dmm'], 'b.-'
        )
        self.ax1.set_xlabel('Gate Voltage / V')
        self.ax1.set_ylabel('DMM Reading / V')

        # Conductivity plot
        conductivity = self._conductivity(self.data['dmm'])
        # conductivity = [0] * len(self.data['dmm'])
        # for i in range(0, len(self.data['dmm'])):
        #    conductivity[i] = 1/self.data['dmm'][i]
        self.ax2 = self.fig.add_subplot(3, 1, 2)
        (self.gate_conductivity_plot,) = self.ax2.plot(
            self.data['gate'], conductivity, 'k.-'
        )
        self.ax2.set_xlabel('Gate Voltage / V')
        self.ax2.set_ylabel('Conductivity / a.u.')

        # Time plot
        self.ax3 = self.fig.add_subplot(3, 1, 3)
        (self.dmm_plot,) = self.ax3.plot(
            self.data['time'], self.data['dmm'], 'r.', label='DMM'
        )
        self.ax3_2 = self.ax3.twinx()
        (self.gate_plot,) = self.ax3_2.plot(
            self.data['time'], self.data['gate'], 'b.', label='Gate (r)'
        )
        self.ax3.set_xlabel('Time / s')
        self.ax3.set_ylabel('DMM Reading (Red)')
        self.ax3_2.set_ylabel('Gate (Blue)')
        # self.ax3.legend(loc = 2,prop={"size":8})

        self.fig.canvas.mpl_connect('close_event', self.on_close)
        # plt.draw()
        # plt.pause(0.01)
        # plt.clf()
        return

    def read_data(self):
        self._clear_data()
        with open('spectrum.csv', 'r', newline='\n') as csvfile:
            reader = csv.reader(csvfile, delimiter=';',
                                quoting=csv.QUOTE_NONNUMERIC)
            for row in reader:
                self.data['time'].append(row[0])
                self.data['gate'].append(row[1])
                self.data['dmm'].append(row[2])


if __name__ == '__main__':
    plot = Plotter()

    plot.read_data()
    plot.plot_spectrum()
    # plot.running = False
    while plot.running:
        time.sleep(0.5)
        try:
            plot.update_spectrum()
        except Exception:
            pass
