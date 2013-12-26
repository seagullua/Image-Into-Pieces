from wand.image import Image
import math

class Slice:
    """
    @type slice Image
    """
    slice = None
    output_name = ''
    width = 0
    height = 0
    x = 0
    y = 0

    def __init__(self, x_, y_, width_, height_):
        self.x = x_
        self.y = y_
        self.width = width_
        self.height = height_

    def __repr__(self):
        return '{name}: w={width} h={height} x={x} y={y}'.format(
            name=self.output_name, width=self.width, height=self.height,
            x=self.x, y=self.y)

def sliceImage(source_name, slice_size, slice_name, slice_format, compression_quality=100):
    output_name = '{name}_{x}_{y}.{format}'.format(name=slice_name,
                                                   format=slice_format,
                                                   x='{x}',
                                                   y='{y}')
    info_name = '{name}.slice'.format(name=slice_name)

    image = Image(filename=source_name)
    slice_size = int(slice_size)
    width = int(image.width)
    height = int(image.height)

    vertical_slices = int(math.ceil(height / slice_size))
    horizontal_slices = int(math.ceil(width / slice_size))

    slices = []

    for x in range(0, horizontal_slices):
        for y in range(0, vertical_slices):
            slice = Slice(x * slice_size,
                          y * slice_size,
                          min(width - x * slice_size, slice_size),
                          min(height - y * slice_size, slice_size))
            slice.output_name = output_name.format(x=x, y=y)
            slices.append(slice)

    f = open(info_name, 'w')
    f.write('{width} {height} {slices}\n'.format(width=width,
                                                 height=height,
                                                 slices=len(slices)))
    for s in slices:
        cropped = image.clone()
        cropped.crop(s.x,
                     s.y,
                     width=s.width,
                     height=s.height)
        cropped.compression_quality = compression_quality
        cropped.save(filename=s.output_name)
        f.write('{x} {y} {width} {height} {name}\n'.format(
            x=s.x, y=s.y, width=s.width, height=s.height,
            name=s.output_name
        ))




sliceImage('image.jpg', slice_size=512, slice_name="out",
           slice_format="jpg", compression_quality=55)
