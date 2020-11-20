# pixtolic

This is a project for playing with images and nmigen / cool FPGA tools
and learning as I go. Here is a summary of roughly what is going on

## setup

You need to install
[yosys](https://nmigen.info/nmigen/latest/install.html) and
[nmigen](https://nmigen.info/nmigen/latest/install.html). For handling
image data [numpy](https://numpy.org/) and
[pillow](https://python-pillow.org) are also used. You probably also
want [GTKWave](http://gtkwave.sourceforge.net/) for viewing simulation
waveforms.

## compile and download (to iCEBreaker)

Run `python -m pixtolic.top`. This should build the design and flash
it to an attached iCEBreaker board (currently the only target.

## simulating a module

Some modules include simulations, you can run these with e.g. `python
-m pixtolic.sources.still`. This will produce a `still.vcd` waveform
file which you can view with `gtkwave still.vcd`.

## structure

The `pixtolic/top.py` file gives the top-level structure of the
design. It assumes you are using a 12-bit color VGA output pmod as
sold by
[Digilent](https://store.digilentinc.com/pmod-vga-video-graphics-array/). You
can also use a 12-bit color "DVI pmod" with an HDMI connector as made
by
[1bitsquared](https://1bitsquared.com/collections/fpga/products/pmod-digital-video-interface)
(requires different pin assignments -- will add shortly). Whenever the
24-bit color DDR DVI pmod becomes available I will support that also,
everything is designed to be generic in the color depth. Assuming
we've told the compiler with the different types of IO resources
available on the board, we can get groups of pins by name with
`platform.request`. `Cat` is an nmigen function for concatenating
signals together.

```python
clk12 = platform.request('clk12', dir='-')
vga_pads = platform.request('vga')
uart_pads = platform.request('uart')
leds = Cat([
     platform.request('led_r'),
     platform.request('led_g'),
])
button = platform.request('button')
```

The first thing is to define the clock domains and use the iCE40's PLL
to synthesize a pixel clock (36 MHz for 800x600p @ 56Hz) from the
crystal oscillator clock on the iCEbreaker board (12 MHz).
I've defined some objects for storing the [VGA timing
data](http://www.tinyvga.com/vga-timing). Available resolutions are
basically limited by which pixel clock frequencies you can generate.

```python
# this resolution uses a 36 MHz pixel clock, which the PLL can
# match exactly
res = resolutions[ResolutionName.SVGA_800_600p_56hz]

# define clock domains called 'pixel' and 'sync'
# 'sync' will run at 12 MHz and can be used for
# other logic
m.domains.pixel = ClockDomain()
m.domains.sync = sync = ClockDomain()

# this class sets parameters for a special PLL tile
# that generates a higher frequency clock, as well as a 
# buffered copy of its input clock as `buf_clkin`. we set the
# high frequency output clock as the clock for the 'pixel' domain
# and the `buf_clkin` signal as the clock for the 'sync' domain
m.submodules.pll = pll = iCE40PLL(
    freq_in_mhz=12,
    freq_out_mhz=res.pixclk_freq / 1e6,
    domain_name='pixel',
)
m.d.comb += [
    pll.clk_pin.eq(clk12),
    sync.clk.eq(pll.buf_clkin),
]
# we also need to tell the compiler this clock is 36 MHz
# so it can check if the design meets timing constraints
platform.add_clock_constraint(pll.clk_pin, res.pixclk_freq)
```

Next we add some submodules to the design. The `VgaTiming` module
generates hsync / vsync / active signals for the given resolution.
The `TestPattern` module generates a simple pattern of color swatches.
For the `Still` module we can pass in a sufficiently small `PIL.Image`
object and it will load it into the FPGA's block RAM when we reflash
the chip, then read out the image contents repeatedly as the pixel
clock runs.

```python
m.submodules.vga_timing = vga_timing = VgaTiming(res)
m.submodules.test_pattern = test_pattern = TestPattern(vga_timing, color_depth=self.color_depth)

fname = path.join(
    path.dirname(__file__),
    '../resources/RGB_12bits_parrot.png',
)
image = Image.open(fname).resize((100, 75))
m.submodules.still = still = Still(
    timing=vga_timing,
    color_depth=self.color_depth,
    image=image,
)
```

Then we just wire up stuff to the IO/pins for the VGA and for the
button on the iCEbreaker board itself (labeled "Button" on the
silkscreen). We'll show the loaded still when the button is held and
show the color bars / swatches otherwise.

```python
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
```

Finally there is a UART module included which is just set in loopback
mode right now, because that seems like it could also be useful. You
could take it out and reclaim some more FPGA space for larger still
storage or something. Internally it calculates the UART baud rate by
just dividing down the 12 MHz clock with registers, since there's only
one PLL on the iCE40. When the design is running, you can access this
UART over USB by running `screen /dev/ttyUSB0 115200` (you might get a
different `ttyUSB*` number). Then anything you type will get echoed
back by the FPGA and the red and green lights on the board will flash
-- use `ctrl+a k y` to exit `screen`.

```python
m.submodules.uart = uart = UARTLoopback(
    uart_pads,
    clk_freq=12e6,
    baud_rate=115200,
)
m.d.comb += [
    leds.eq(uart.rx_data[0:2]),
]
```

Everything else that's going on right now is pretty much the actual
pixel generation logic in the `pixtolic/sources/patterns.py` and
`pixtolic/sources/still.py` modules.