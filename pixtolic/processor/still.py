from itertools import chain, repeat

from nmigen import *

class Still(Elaboratable):
    
    def __init__(self, timing, pixel_depth):
        self.timing = timing
        rep = timing.res.width // 16
        init = list(chain(*(repeat(i, rep) for i in range(16)))) 
        # white = 2 ** 4 - 1
        # init = [(i * white) // timing.res.width for i in range(timing.res.width)]
        # for j in range(timing.res.height):
        #     for i in range(timing.res.width):
        #         init.append((i * white) // timing.res.width)
        self.pixcount = timing.res.width
        self.memory = Memory(
            width=pixel_depth,
            depth=self.pixcount,
            init=init,
        )
        # self.pixval = Signal(pixel_depth)
        self.red = Signal(4)
        self.green = Signal(4)
        self.blue = Signal(4)
        self.addr = Signal(range(self.pixcount))

    def elaborate(self, platform):
        m = Module()
        
        rd_port = self.memory.read_port(domain='pixel')
        m.submodules += rd_port
        m.d.comb += [
            rd_port.addr.eq(self.addr),
            self.red.eq(rd_port.data),
            self.green.eq(rd_port.data),
            self.blue.eq(rd_port.data),
        ]
        with m.If(self.timing.active):
            with m.If(self.addr == self.pixcount - 1):
                m.d.pixel += self.addr.eq(0)
            with m.Else():
                m.d.pixel += self.addr.eq(self.addr + 1)

        return m
