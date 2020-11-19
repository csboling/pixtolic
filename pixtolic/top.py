from nmigen import *
from nmigen_boards.icebreaker import ICEBreakerPlatform

from pixtolic.config.resolutions import ResolutionName, resolutions
from pixtolic.device.iCE40 import iCE40PLL
from pixtolic.device.icebreaker import vga_pmod
from pixtolic.output.timing import VgaTiming
from pixtolic.patterns import TestPattern
from pixtolic.processor.still import Still
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
        button = platform.request('button')

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
        m.submodules.test_pattern = test_pattern = TestPattern(vga_timing, color_depth=self.color_depth)
        m.submodules.still = still = Still(vga_timing, pixel_depth=self.color_depth * 3)

        m.d.comb += [
            vga_pads.hsync.eq(vga_timing.hsync),
            vga_pads.vsync.eq(vga_timing.vsync),
        ]
        with m.If(button):
            m.d.comb += [
                vga_pads.red.eq(still.red),
                vga_pads.green.eq(still.green),
                vga_pads.blue.eq(still.blue),
            ]
        with m.Else():
            m.d.comb += [
                vga_pads.red.eq(test_pattern.red),
                vga_pads.green.eq(test_pattern.green),
                vga_pads.blue.eq(test_pattern.blue),
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
    platform.add_resources(platform.break_off_pmod)
    products = platform.build(top, do_build=True, do_program=False)
    platform.toolchain_program(products, 'top')
