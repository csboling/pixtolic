from nmigen.build import *

vga_pmod = [
    Resource(
        'vga', 0,
        Subsignal(
            'hsync', 
            # PMOD1B:4
            Pins(
                '7',
                dir='o',
                conn=('pmod', 1),
            ),
            Attrs(IO_STANDARD='SB_LVCMOS33'),
        ),
        Subsignal(
            'vsync',
            Pins(
                # PMOD1B:5
                '8',
                dir='o',
                conn=('pmod', 1),
            ),
            Attrs(IO_STANDARD='SB_LVCMOS33'),
        ),
        # Subsignal(
        #     'pixclk',
        #     Pins(
        #         # PMOD1B:6 (NC)
        #         '9',
        #         dir='o',
        #         conn=('pmod', 1),
        #     ),
        #     Attrs(IO_STANDARD='SB_LVCMOS33'),
        # ),
        # Subsignal(
        #     'active',
        #     Pins(
        #         # PMOD1B:7 (NC)
        #         '10',
        #         dir='o',
        #         conn=('pmod', 1),
        #     ),
        #     Attrs(IO_STANDARD='SB_LVCMOS33'),
        # ),

        Subsignal(
            'red',
            Pins(
                # PMOD1A:0 PMOD1A:1 PMOD1A:2 PMOD1A:3
                '1 2 3 4',
                dir='o',
                conn=('pmod', 0),
            ),
            Attrs(IO_STANDARD='SB_LVCMOS33'),
        ),
        Subsignal(
            'green', 
            Pins(
                # PMOD1B:0 PMOD1B:1 PMOD1B:2 PMOD1B:3
                '1 2 3 4',
                dir='o',
                conn=('pmod', 1),
            ),
            Attrs(IO_STANDARD='SB_LVCMOS33'),
        ),
        Subsignal(
            'blue',
            Pins(
                # PMOD1A:4 PMOD1A:5 PMOD1A:6 PMOD1A:7
                '7 8 9 10',
                dir='o',
                conn=('pmod', 0),
            ),
            Attrs(IO_STANDARD='SB_LVCMOS33'),
        ),
    ),
]
