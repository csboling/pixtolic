def vga_layout(color_depth):
    return [
        ('hsync', 1),
        ('vsync', 1),
        ('red', color_depth),
        ('green', color_depth),
        ('blue', color_depth),
    ]
