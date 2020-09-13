from dataclasses import dataclass
from enum import Enum


@dataclass
class ScanTimings:
    sync_pulse: int
    back_porch: int
    visible: int
    front_porch: int

    @property
    def prescan(self):
        return self.sync_pulse + self.back_porch

    @property
    def overscan(self):
        return self.prescan + self.front_porch

    @property
    def fullscan(self):
        return self.overscan + self.visible

class VgaResolution:
    def __init__(self, pixclk_freq, h_timings, v_timings):
        self.pixclk_freq = pixclk_freq
        self.h = h_timings
        self.v = v_timings
        self.width = self.h.visible
        self.height = self.v.visible


class ResolutionName(Enum):
    VGA_640_480p_60hz    = 0
    SVGA_800_600p_60hz   = 1
    XGA_1024_768p_60hz   = 2
    VESA_1280_960p_60hz  = 3
    VESA_1280_1024p_60hz = 4
    VESA_1600_1200p_60hz = 5


# thanks http://www.tinyvga.com !
resolutions = {
    ResolutionName.VGA_640_480p_60hz: VgaResolution(
        pixclk_freq=25.175e6,
        h_timings=ScanTimings(
            sync_pulse=96,
            back_porch=48,
            visible=640,
            front_porch=16,
        ),
        v_timings=ScanTimings(
            sync_pulse=2,
            back_porch=33,
            visible=480,
            front_porch=10,
        ),

        # works

        # clkout_freq: 25.12MHz
        # divq       : 5
        # vco        : 804.00MHz
        # divr       : 0
        # divf       : 66

    ),
    ResolutionName.SVGA_800_600p_60hz: VgaResolution(
        pixclk_freq=40e6,
        h_timings=ScanTimings(
            sync_pulse=128,
            back_porch=88,
            visible=800,
            front_porch=40,
        ),
        v_timings=ScanTimings(
            sync_pulse=4,
            back_porch=23,
            visible=600,
            front_porch=1,
        ),

        # works, some transition glitches?

        # clkout_freq: 39.75MHz
        # divq       : 4
        # vco        : 636.00MHz
        # divr       : 0
        # divf       : 52
    ),

    ResolutionName.XGA_1024_768p_60hz: VgaResolution(
        pixclk_freq=65e6,
        h_timings=ScanTimings(
            sync_pulse=136,
            back_porch=160,
            visible=1024,
            front_porch=24,
        ),
        v_timings=ScanTimings(
            sync_pulse=6,
            back_porch=29,
            visible=768,
            front_porch=3,
        ),

        # works

        # clkout_freq: 64.50MHz
        # divq       : 4
        # vco        : 1032.00MHz
        # divr       : 0
        # divf       : 85
        
    ),

    ResolutionName.VESA_1280_960p_60hz: VgaResolution(
        pixclk_freq=108e6,
        h_timings=ScanTimings(
            sync_pulse=136,
            back_porch=216,
            visible=1280,
            front_porch=80,
        ),
        v_timings=ScanTimings(
            sync_pulse=3,
            back_porch=30,
            visible=960,
            front_porch=1,
        ),

        # no picture

        # INFO:iCE40PLL:Config:
        # clkout_freq: 108.00MHz
        # divq       : 3
        # vco        : 864.00MHz
        # divr       : 0
        # divf       : 71
    ),

    ResolutionName.VESA_1280_1024p_60hz: VgaResolution(
        pixclk_freq=108e6,
        h_timings=ScanTimings(
            sync_pulse=112,
            back_porch=248,
            visible=1280,
            front_porch=48,
        ),
        v_timings=ScanTimings(
            sync_pulse=3,
            back_porch=38,
            visible=1024,
            front_porch=1,
        ),

        # no picture

        # clkout_freq: 108.00MHz
        # divq       : 3
        # vco        : 864.00MHz
        # divr       : 0
        # divf       : 71
    ),
    
    ResolutionName.VESA_1600_1200p_60hz: VgaResolution(
        pixclk_freq=162e6,
        h_timings=ScanTimings(
            sync_pulse=192,
            back_porch=304,
            visible=1600,
            front_porch=64,
        ),
        v_timings=ScanTimings(
            sync_pulse=3,
            back_porch=46,
            visible=1200,
            front_porch=1,
        ),

        # 'input not supported' on acer LCD

        # clkout_freq: 162.00MHz
        # divq       : 2
        # vco        : 648.00MHz
        # divr       : 0
        # divf       : 53
    ),
}
