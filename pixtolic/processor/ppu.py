from nmigen import *

from pixtolic.processor.alu import PixelALU


class PixelProcessingUnit(Elaboratable):
    def __init__(self, resolution, pixel_depth, stride, program_mem):
        self.resolution = resolution
        self.pixel_depth = pixel_depth
        self.stride = stride
        self.program_mem = program_mem

        # inputs
        self.en = Signal()
        self.new_frame = Signal()
        self.new_batch = Signal()

        self.mem_rd = self.program_mem.read_port()
        self.pc = Signal(program_mem.addr_width)
        self.instruction = Signal(program_mem.data_width)
        self.output_reg = Signal(self.pixel_depth)

        self.frame_counter = Signal(32)
        self.y_pos = Signal(max=self.resolution.height)
        self.x_pos = [Signal(max=self.resolution.width) for lane in range(self.stride)]
        self.new_line = Signal()
        self.result = Signal(self.stride * self.pixel_depth)

    def elaborate(self):
        m = Module()

        m.submodules.mem_rd = self.mem_rd
        m.comb += [
            self.mem_rd.addr.eq(self.pc),
            self.instruction.eq(self.mem_rd.data),
            self.new_line.eq(self.x_pos[0] == self.resolution.width - self.stride),
        ]

        for lane in range(self.stride):
            with m.If(self.new_frame | self.new_line):
                m.sync.pixel += self.x_pos[lane].eq(lane)
            with m.Elif(self.new_batch):
                m.sync.pixel += self.x_pos[lane].eq(self.x_pos[lane] + self.stride)

            alu = PixelALU(
                instruction=self.instruction,
                x_pos=self.x_pos[lane],
                y_pos=self.y_pos,
                frame=self.frame_counter,
            )
            m.submodules += alu
            m.comb += self.result[lane * self.pixel_depth : (lane + 1) * self.pixel_depth].eq(alu.result)
            
        with m.If(self.new_frame):
            m.sync.pixel += [
                self.pc.eq(0),
                self.y_pos.eq(0),
                self.frame_counter.eq(self.frame_counter + 1),
            ]
        with m.Elif(self.pc != self.PROGRAM_LEN):
            m.sync.pixel += [
                self.pc.eq(self.pc + 1),
            ]

        return m
