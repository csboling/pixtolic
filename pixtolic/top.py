from nmigen import *
from nmigen_boards.icebreaker import ICEBreakerPlatform

from pixtolic.config.resolutions import ResolutionName, resolutions
from pixtolic.device.iCE40 import iCE40PLL
from pixtolic.device.icebreaker import vga_pmod
from pixtolic.output.timing import VgaTiming
from pixtolic.patterns import TestPattern


class PixtolicTop(Elaboratable):
    def __init__(self, color_depth):
        self.color_depth = color_depth

    def elaborate(self, platform):
        m = Module()

        m.domains.pixel = ClockDomain()

        pads = platform.request('vga')

        # this resolution uses a 36 MHz pixel clock, which the PLL can
        # match exactly
        res = ResolutionName.SVGA_800_600p_56hz
        m.submodules.vga_timing = vga_timing = VgaTiming(resolutions[res])
        m.submodules.test_pattern = TestPattern(pads, vga_timing, color_depth=self.color_depth)

        m.submodules.pll = pll = iCE40PLL(12e6 / 1e6, vga_timing.res.pixclk_freq / 1e6, 'pixel')
        clk12 = platform.request('clk12', dir='-')
        m.d.comb += pll.clk_pin.eq(clk12)
        platform.add_clock_constraint(pll.clk_pin, vga_timing.res.pixclk_freq)

        
        m.d.comb += [
            pads.hsync.eq(vga_timing.hsync),
            pads.vsync.eq(vga_timing.vsync),
        ]

        return m


if __name__ == '__main__':
    top = PixtolicTop(color_depth=4)
    platform = ICEBreakerPlatform()
    platform.add_resources(vga_pmod)
    products = platform.build(top, do_build=True, do_program=False)
    # products = plan.execute()
    platform.toolchain_program(products, 'top')
