from nmigen import *
from nmigen_boards.icebreaker import ICEBreakerPlatform

from pixtolic.config.resolutions import ResolutionName, resolutions
from pixtolic.device.iCE40 import iCE40PLL
from pixtolic.device.icebreaker import vga_pmod
from pixtolic.output.timing import VgaTiming
from pixtolic.patterns import TestPattern
from pixtolic.ui.uart import UARTLoopback


class PixtolicTop(Elaboratable):
    def __init__(self, color_depth):
        self.color_depth = color_depth

    def elaborate(self, platform):
        m = Module()

        clk12 = platform.request('clk12', dir='-')
        vga_pads = platform.request('vga')
        uart_pads = platform.request('uart')
        leds = Cat([
            platform.request('led_r'),
            platform.request('led_g'),
        ])

        # this resolution uses a 36 MHz pixel clock, which the PLL can
        # match exactly
        res = resolutions[ResolutionName.SVGA_800_600p_56hz]

        m.domains.pixel = ClockDomain()
        m.domains.sync = sync = ClockDomain()
        m.submodules.pll = pll = iCE40PLL(
            freq_in_mhz=12,
            freq_out_mhz=res.pixclk_freq / 1e6,
            domain_name='pixel',
        )
        m.d.comb += [
            pll.clk_pin.eq(clk12),
            sync.clk.eq(pll.buf_clkin),
        ]
        platform.add_clock_constraint(pll.clk_pin, res.pixclk_freq)

        m.submodules.vga_timing = vga_timing = VgaTiming(res)
        m.submodules.test_pattern = TestPattern(vga_pads, vga_timing, color_depth=self.color_depth)
        m.d.comb += [
            vga_pads.hsync.eq(vga_timing.hsync),
            vga_pads.vsync.eq(vga_timing.vsync),
        ]

        m.submodules.uart = uart = UARTLoopback(
            uart_pads,
            clk_freq=12e6,
            baud_rate=115200,
        )
        m.d.comb += [
            leds.eq(uart.rx_data[0:2]),
        ]

        return m


if __name__ == '__main__':
    top = PixtolicTop(color_depth=4)
    platform = ICEBreakerPlatform()
    platform.add_resources(vga_pmod)
    products = platform.build(top, do_build=True, do_program=False)
    # products = plan.execute()
    platform.toolchain_program(products, 'top')
