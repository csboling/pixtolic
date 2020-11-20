from nmigen import *
from nmigen.cli import main
from nmigen.sim.pysim import Simulator

from pixtolic.config.resolutions import resolutions, ResolutionName
from pixtolic.processor.alu import (
    PixelALU,
    PixelOperand,
    PixelDestination,
    PixelOpcode,
    pixel_instruction_layout,
    REGISTER_WIDTH,
)
from pixtolic.output.timing import VgaTiming
from pixtolic.util import int_for


class PixelProcessor(Elaboratable):

    def __init__(self, timing, num_pixels, pixel_width, pixel_depth):
        self.timing = timing
        self.num_pixels = num_pixels
        self.pixel_width = pixel_width
        self.output_width = self.num_pixels * self.pixel_width
        self.pixel_depth = pixel_depth

        # inputs
        self.new_frame = Signal()
        self.active = Signal()
        self.start_next_batch = Signal()

        # outputs
        self.result = Signal(self.output_width)
        self.result_ready = Signal()

        self.instruction_width = 46
        self.max_instructions = self.instruction_depth = 2
        self.pc = Signal(range(self.instruction_depth))
        self.instruction = Signal(self.instruction_width)
        self.y_coord = Signal(32)
        self.f_number = Signal(32)
        self.x_coord = [Signal(32) for _ in range(self.num_pixels)]
        self.end_of_line = Signal()
        
    def elaborate(self, platform):
        m = Module()

        for lane in range(self.num_pixels):
            with m.If(self.timing.active):
                with m.If(self.new_frame | (self.end_of_line & self.start_next_batch)):
                    m.d.pixel += self.x_coord[lane].eq(lane)
                with m.Elif(self.start_next_batch):
                    m.d.pixel += self.x_coord[lane].eq(self.x_coord[lane] + self.num_pixels)

            alu = PixelALU(self.pixel_depth)
            m.d.comb += [
                alu.instruction.eq(self.instruction),
                alu.x_pos.eq(self.x_coord[lane]),
                alu.y_pos.eq(self.y_coord),
                alu.frame.eq(self.f_number),
            ]
            m.submodules += alu

        max_instructions = self.num_pixels * 2
        instruction = Record(pixel_instruction_layout)
        instruction_mem = Memory(
            width=self.instruction_width,
            depth=self.instruction_depth,
            init=[
                int_for(
                    instruction.layout,
                    left_op=PixelOperand.XPOS.value,
                    right_op=PixelOperand.YPOS.value,
                    dest=PixelDestination.GP0.value,
                    opcode=PixelOpcode.SUB.value,
                    immediate=0,
                ),
                int_for(
                    instruction.layout,
                    left_op=PixelOperand.GP0.value,
                    right_op=PixelOperand.IMM.value,
                    dest=PixelDestination.OUTPUT.value,
                    opcode=PixelOpcode.GT.value,
                    immediate=0,
                ),
            ]
        )
        rd_port = instruction_mem.read_port(domain='pixel')
        m.submodules += rd_port
        m.d.comb += [
            rd_port.addr.eq(self.pc),
            self.instruction.eq(rd_port.data),
        ]

        m.d.comb += [
            self.result_ready.eq(self.pc == self.max_instructions-1),
            self.end_of_line.eq(self.x_coord[0] == 640 - self.num_pixels),
        ]

        with m.If(
            (self.timing.line_counter >= self.timing.res.v.prescan)
            & (self.timing.scan_counter >= self.timing.res.h.prescan-1)
        ):
            with m.If(self.start_next_batch):
                m.d.pixel += self.pc.eq(0)
            with m.Elif(~self.result_ready):
                m.d.pixel += self.pc.eq(self.pc + 1)

        with m.If(self.new_frame):
            self.f_number.eq(self.f_number + 1)
        with m.Elif(self.active):
            with m.If(self.end_of_line & self.start_next_batch):
                self.y_coord.eq(self.y_coord + 1)

        return m

def ppu_tb(dut):
    # yield
    # yield dut.ppu.new_frame.eq(1)
    # yield
    # yield dut.ppu.new_frame.eq(0)
    # for _ in range(20):
    #     yield
    # yield ppu.new_frame.eq(1)
    # # yield ppu.new_batch.eq(1)
    # yield
    # # yield ppu.new_frame.eq(0)
    # # yield ppu.new_batch.eq(0)
    # yield
    # yield
    # yield ppu.new_frame.eq(0)
    # yield
    for _ in range(800 * 40):
        yield

class TestBench(Elaboratable):
    def __init__(self, ppu, vga):
        self.ppu = ppu
        self.vga = vga

    def elaborate(self, platform):
        m = Module()

        m.submodules += [
            self.ppu,
            self.vga,
        ]
        m.d.comb += [
            self.ppu.start_next_batch.eq(self.vga.new_frame | (self.ppu.result_ready & self.vga.active)),
            self.ppu.new_frame.eq(self.vga.new_frame),
            self.ppu.active.eq(self.vga.active | self.vga.new_line),
        ]
        return m

if __name__ == '__main__':
    res = resolutions[ResolutionName.VGA_640_480p_60hz]
    # instruction = Record(pixel_instruction_layout)
    # program_mem = Memory(
    #     width=len(instruction),
    #     depth=2,
    #     init=[
    #         int_for(
    #             instruction.layout,
    #             left_op=PixelOperand.XPOS.value,
    #             right_op=PixelOperand.YPOS.value,
    #             dest=PixelDestination.GP0.value,
    #             opcode=PixelOpcode.SUB.value,
    #             immediate=0,
    #         ),
    #         int_for(
    #             instruction.layout,
    #             left_op=PixelOperand.GP0.value,
    #             right_op=PixelOperand.IMM.value,
    #             dest=PixelDestination.OUTPUT.value,
    #             opcode=PixelOpcode.GT.value,
    #             immediate=0,
    #         ),
    #     ],
    # )
    timing = VgaTiming(res)
    dut = TestBench(
        PixelProcessor(
            timing,
            num_pixels=8,
            pixel_width=12,
            pixel_depth=4,
            # resolution=res,
            # pixel_depth=4,
            # stride=4,
            # instruction_depth=program_mem.depth,
            # program_mem=program_mem,
        ),
        timing,
        # PixelFifo(width=16, depth=16),
    )

    sim = Simulator(dut)
    def proc():
        yield from ppu_tb(dut)
    sim.add_clock(1e-6, domain='pixel')
    sim.add_sync_process(proc, domain='pixel')
    with sim.write_vcd('ppu.vcd'):
        sim.run()
