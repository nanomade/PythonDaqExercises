# -*- coding: utf-8 -*-
import csv
import time
import datetime

import numpy as np
import pyvisa


class SimpleIV:
    def __init__(self):
        rm = pyvisa.ResourceManager()

        res = rm.list_resources()
        for instr in res:
            # print(instr)
            if 'USB' in instr:
                self.gate = rm.open_resource(instr)

        self.gate.write('FUNCTION DC')

        self.dmm = rm.open_resource('COM1')
        self.dmm.stop_bits = pyvisa.constants.StopBits.two
        self.dmm.parity = pyvisa.constants.Parity.none
        self.dmm.timeout = 5000
        self.dmm.read_termination = '\n'
        self.dmm.write_termination = '\n'
        self.dmm.write('SYST:REM')
        self.dmm.write('*CLS')
        time.sleep(0.5)

    @staticmethod
    def _calculate_steps_bak(v_low, v_high, step_size, repeats):
        # From 0 to v_high
        up = list(np.arange(0, v_high, step_size))
        # v_high -> 0
        down = list(np.arange(v_high, 0, -1 * step_size))

        # N * (v_high -> v_low -> v_high)
        zigzag = (
            list(np.arange(v_high, v_low, -1 * step_size))
            + list(np.arange(v_low, v_high, step_size))
        ) * repeats

        step_list = up + zigzag + down + [0]
        return step_list

    @staticmethod
    def _calculate_steps(v_low, v_high, step_size, repeats):
        single = (
            list(np.arange(0, v_high, step_size))
            + list(np.arange(v_high, v_low, -1 * step_size))
            + list(np.arange(v_low, 0, step_size))
        )
        step_list = single * repeats + [0]
        return step_list

    def instrument_id(self):
        """
        Prints the ID string of DMM and gate to the terminal.
        """
        print(self.gate.query('*IDN?').strip())
        print(self.dmm.query('*IDN?').strip())
        return True

    def set_gate_value(self, value: float):
        """
        Set the gate value. Allowed values are between 0 and 2
        :param value: The gate value to apply
        :return: True if values was legal, otherwise False
        """
        success = False
        if -5 < value < 5:
            self.gate.write('SOURCE1:VOLTAGE:OFFSET {}'.format(value))
            success = True
        return success

    def measure_dmm(self):
        """
        Measure the current on the DMM.
        It is assumed that the user appled the correct instrument
        setting beforehand.
        """
        self.dmm.write('READ?')
        time.sleep(0.05)
        value_raw = self.dmm.read()
        value = float(value_raw)
        return value

    def _gated_measurement(self, gate_steps):
        # This is a bit of a mess, csv-export and data export
        # is more intermixed than what you would ideally want...

        self.measure_dmm()  # Ensure to start with a fresh reading
        t_start = time.time()
        now = datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S')
        filename = 'data_' + now + '.csv'
        with open('spectrum.csv', 'w', newline='\n') as csvfile, open(
            filename, 'w', newline='\n'
        ) as csvfile2:
            writer = csv.writer(csvfile, delimiter=';')
            writer2 = csv.writer(csvfile2, delimiter=';')
            for v_gate in gate_steps:
                self.set_gate_value(v_gate)
                time.sleep(0.01)
                dmm_reading = self.measure_dmm()
                print(v_gate, dmm_reading)
                dt = time.time() - t_start

                writer.writerow([dt, v_gate, dmm_reading])
                writer2.writerow([dt, v_gate, dmm_reading])
                csvfile.flush()
                csvfile2.flush()

    def iv_measurement(self, v_from, v_to, stepsize, repeats=1):
        if stepsize < 1e-4:
            print('Stepsize too small!')
            return
        if stepsize > 0.025:
            print('Stepsize to large!')
            return

        gate_steps = self._calculate_steps(v_from, v_to, stepsize, repeats)
        self._gated_measurement(gate_steps)

    def constant_gate_measurement(self, gate_v=0, constant_steps=100):
        sign = np.sign(gate_v)
        up = list(np.arange(0, gate_v, 0.01 * sign)) + [gate_v]
        down = list(np.arange(gate_v, 0, -0.01 * sign)) + [0]
        constant = [gate_v] * constant_steps
        gate_steps = up + constant + down
        self._gated_measurement(gate_steps)


if __name__ == '__main__':
    iv = SimpleIV()

    iv_measurement = True
    constant_gate = False

    iv.instrument_id()
    if iv_measurement:
        iv.iv_measurement(v_from=0, v_to=1.1, stepsize=0.01, repeats=1)

    if constant_gate:
        iv.constant_gate_measurement(gate_v=-0.6, constant_steps=100)
