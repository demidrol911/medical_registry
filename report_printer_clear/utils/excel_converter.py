VERTICAL_ALIGN_MAP = {
    0: 'vleft', 1: 'vcenter',
    2: 'vcenter', 4: 'vcenter'
}
HORIZONTAL_ALIGN_MAP = {
    0: 'left', 1: 'left',
    2: 'center', 3: 'right',
    5: 'left'
}
WIDTH_MULTIPLIER = 223
HEIGHT_MULTIPLIER = 20


def convert_colour(colour):
    red = convert_colour_component(colour[0])
    green = convert_colour_component(colour[1])
    blue = convert_colour_component(colour[2])
    colour_code = '#%s%s%s' % (red, green, blue)
    return colour_code


def convert_colour_component(colour_component):
    colour_code = str(hex(colour_component))[2:]
    if len(colour_code) == 1:
        colour_code = '0' + colour_code
    return colour_code


def convert_vertical_align(vertical_align):
    return VERTICAL_ALIGN_MAP[vertical_align]


def convert_horizontal_align(horizontal_align):
    return HORIZONTAL_ALIGN_MAP[horizontal_align]


def convert_cell_width(original_width):
    width = 0
    if original_width:
        width = original_width / WIDTH_MULTIPLIER
    return width


def convert_cell_height(original_height):
    height = 0
    if original_height:
        height = original_height / HEIGHT_MULTIPLIER
    return height


def convert_bold(original_bold):
    if original_bold == 400:
        return False
    elif original_bold == 700:
        return True
    else:
        return False