from functools import reduce

from nmigen import *


class VgaTiming(Elaboratable):
    
    def __init__(self, resolution):
        self.res = resolution
        self.hsync = Signal()
        self.vsync = Signal()
        self.active = Signal()

        self.scan_counter = Signal(range(self.res.width + self.res.h.overscan))
        self.line_counter = Signal(range(self.res.height + self.res.v.overscan))
        self.x_pos = Signal(range(self.res.width))
        self.y_pos = Signal(range(self.res.height))
        self.new_frame = Signal()
        self.new_line = Signal()

    def elaborate(self, platform):
        m = Module()

        with m.If(self.scan_counter == self.res.width + self.res.h.overscan - 1):
            m.d.pixel += self.scan_counter.eq(0)
            with m.If(self.line_counter == self.res.height + self.res.v.overscan - 1):
                m.d.pixel += [
                    self.line_counter.eq(0),
                ]
            with m.Else():
                m.d.pixel += [
                    self.line_counter.eq(self.line_counter + 1),
                ]
        with m.Else():
            m.d.pixel += [
                self.scan_counter.eq(self.scan_counter + 1),
            ]

        m.d.comb += [
            self.active.eq(reduce(
                lambda x, y: x & y,
                [
                    self.line_counter >= self.res.v.prescan,
                    self.line_counter < self.res.v.prescan + self.res.height,
                    self.scan_counter >= self.res.h.prescan,
                    self.scan_counter < self.res.h.prescan + self.res.width,
                ]
            )),
            self.new_line.eq((self.line_counter >= self.res.v.prescan) & (self.scan_counter == self.res.h.prescan - 1)),
            self.new_frame.eq((self.line_counter == self.res.v.prescan) & (self.scan_counter == self.res.h.prescan - 1)), # (self.scan_counter == 0) & (self.line_counter == 0)),
            self.hsync.eq(~(self.scan_counter < self.res.h.sync_pulse)),
            self.vsync.eq(~(self.line_counter < self.res.v.sync_pulse)),
        ]

        with m.If(self.scan_counter > self.res.h.prescan + self.res.width):
            m.d.comb += self.x_pos.eq(self.res.width)
        with m.Elif(self.scan_counter > self.res.h.prescan):
            m.d.comb += self.x_pos.eq(self.scan_counter - self.res.h.prescan)
        with m.Else():
            m.d.comb += self.x_pos.eq(0)

        with m.If(self.line_counter > self.res.v.prescan + self.res.height):
            m.d.comb += self.y_pos.eq(self.res.height)
        with m.Elif(self.line_counter > self.res.v.prescan):
            m.d.comb += self.y_pos.eq(self.line_counter - self.res.v.prescan)
        with m.Else():
            m.d.comb += self.y_pos.eq(0)

        return m
