from nmigen import *


class TestPattern(Elaboratable):
    def __init__(self, pads, timing, color_depth):
        self.pads = pads
        self.timing = timing
        self.color_depth = color_depth

    def elaborate(self, platform):
        m = Module()

        cells_across = 2 ** self.color_depth
        cells_down = 8
        cell_width = round(self.timing.res.width / cells_across)
        cell_height = round(self.timing.res.height / cells_down)

        red = Signal(self.color_depth)
        green = Signal(self.color_depth)
        blue = Signal(self.color_depth)
        pix_count = Signal(range(cell_width))
        line_count = Signal(range(cell_height))

        cell_col_count = Signal(range(cells_across))
        cell_row_count = Signal(range(cells_down))

        m.d.comb += [
            self.pads.red.eq(red),
            self.pads.green.eq(green),
            self.pads.blue.eq(blue),
            # self.pads.red.eq(self.timing.line_counter),
            # self.pads.green.eq(self.timing.line_counter),
            # self.pads.blue.eq(self.timing.line_counter),
        ]

        with m.If(self.timing.active == 0):
            m.d.pixel += [
                cell_col_count.eq(cells_across-1),
                pix_count.eq(0),
                red.eq(0),
                green.eq(0),
                blue.eq(0),
            ]
        with m.Else():
            with m.If(pix_count == cell_width-1):
                m.d.pixel += [
                    pix_count.eq(0),
                    cell_col_count.eq(cell_col_count - 1),
                ]
            with m.Else():
                m.d.pixel += pix_count.eq(pix_count + 1)

            with m.If(self.timing.scan_counter == self.timing.res.h.prescan):
                m.d.pixel += line_count.eq(line_count + 1)
                with m.If(line_count == cell_height):
                    m.d.pixel += line_count.eq(0)
                    with m.If(cell_row_count == cells_down-1):
                        m.d.pixel += cell_row_count.eq(0)
                    with m.Else():
                        m.d.pixel += cell_row_count.eq(cell_row_count + 1)

            with m.Switch(cell_row_count):
                for k in range(cells_down):
                    with m.Case(k):
                        m.d.pixel += self.assign_color(
                            k,
                            cell_col_count,
                            (red, green, blue),
                        )

        return m

    def assign_color(self, row, cell_col_count, colors):
        bits = format(row, '03b')
        return [
            color.eq(cell_col_count if bits[i] == '1' else 0)
            for i, color in enumerate(colors)
        ]
