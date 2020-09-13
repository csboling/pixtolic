from nmigen import *
from nmigen.sim.pysim import *

from pixtolic.config.resolutions import resolutions, ResolutionName
from pixtolic.output.timing import VgaTiming
from pixtolic.patterns import TestPattern
from pixtolic.output.vga import vga_layout


class Testbench(Elaboratable):
    def __init__(self, timing, pattern):
        self.timing = timing
        self.pattern = pattern

    def elaborate(self, platform):
        m = Module()
        
        m.submodules += self.timing
        m.submodules += self.pattern

        return m

def vga_lines(dut):
    for _ in range(800 * 600):
        yield

if __name__ == '__main__':
    vga = Record(vga_layout(4))
    timing = VgaTiming(resolutions[ResolutionName.VGA_640_480p_60hz])
    dut = Testbench(timing, TestPattern(vga, timing, 4))
    sim = Simulator(dut)
    def proc():
        yield from vga_lines(dut)
    sim.add_clock(1e-6, domain='pixel')
    sim.add_sync_process(proc, domain='pixel')
    with sim.write_vcd('timing.vcd'):
        sim.run()
