from os import path

from nmigen import *
from nmigen.sim.pysim import Simulator
import numpy as np
from PIL import Image

from pixtolic.output.timing import VgaTiming
from pixtolic.config.resolutions import resolutions, ResolutionName
from pixtolic.host.testvec import gradient

class Still(Elaboratable):
    
    def __init__(self, timing, color_depth, image):
        self.timing = timing
        self.color_depth = color_depth

        arr = np.array(image) // 16
        self.init = self.to_rgb12(arr)
        self.width = image.width
        self.height = image.height
        self.pixcount = self.width * self.height
        
        self.memory = Memory(
            width=self.color_depth * 3,
            depth=self.pixcount,
            init=self.init,
        )

        self.x = Signal(range(self.width))
        self.y = Signal(range(self.height))
        self.red = Signal(4)
        self.green = Signal(4)
        self.blue = Signal(4)
        self.addr = Signal(range(self.pixcount))

    def to_rgb12(self, arr):
        luma = arr.sum(axis=2) // 3
        return luma.flatten().tolist()

    def elaborate(self, platform):
        m = Module()
        
        rd_port = self.memory.read_port(domain='pixel')
        m.submodules += rd_port
        m.d.comb += [
            rd_port.addr.eq(self.addr),
            self.addr.eq(self.y * self.width + self.x), 
        ]

        with m.If(self.timing.active):
            m.d.comb += [
                self.red.eq(rd_port.data),
                self.green.eq(rd_port.data),
                self.blue.eq(rd_port.data),
            ]
        with m.Else():
            m.d.comb += [
                self.red.eq(0),
                self.green.eq(0),
                self.blue.eq(0),
            ]
                
        with m.If(self.timing.new_frame):
            m.d.pixel += [
                self.x.eq(0),
                self.y.eq(0),
            ]
        with m.Elif(self.timing.new_line):
            m.d.pixel += self.x.eq(0)
            with m.If(self.y == self.height - 1):
                m.d.pixel += self.y.eq(0)
            with m.Else():
                m.d.pixel += self.y.eq(self.y + 1)
        with m.Elif(self.timing.active):
            with m.If(self.x == self.width - 1):
                m.d.pixel += self.x.eq(0)
            with m.Else():
                m.d.pixel += self.x.eq(self.x + 1)

        return m

class TestBench(Elaboratable):
    def __init__(self, timing, still):
        self.timing = timing
        self.still = still

    def elaborate(self, platform):
        m = Module()

        m.submodules += [
            self.timing,
            self.still,
        ]

        return m

if __name__ == '__main__':
    color_depth = 4
    image = gradient(color_depth=color_depth)
    timing = VgaTiming(resolutions[ResolutionName.VGA_640_480p_60hz])
    dut = TestBench(
        timing,
        Still(timing, color_depth=color_depth, image=image),
    )

    sim = Simulator(dut)
    def proc():
        for _ in range(800 * 40):
            yield
    sim.add_clock(1e-6, domain='pixel')
    sim.add_sync_process(proc, domain='pixel')
    with sim.write_vcd('still.vcd'):
        sim.run()
