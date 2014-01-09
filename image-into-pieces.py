try:
    from wand.image import Image
    import math
    import os
    import sys
    import errno
    from optparse import OptionParser
except Exception as e:
    print(e.__doc__, file=sys.stderr)
    print(e.__str__(), file=sys.stderr)
    sys.exit(errno.EIO)

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

def sliceImage(source_name,
               slice_size,
               slice_name,
               slice_format,
               binary,
               chunk_size,
               output_directory=".",
               generate_index_file=True,
               compression_quality=100):

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    else:
        #Delete all existing files
        for files in os.listdir(output_directory):
            if files.startswith(slice_name):
                os.remove(os.path.join(output_directory, files))

    output_name = '{name}_{x}_{y}.{format}'.format(
        name=slice_name,
        format=slice_format,
        x='{x}',
        y='{y}')




    info_name = '{name}.slice'.format(name=slice_name)
    print('Opening image')

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

    f = open(os.path.join(output_directory, info_name), 'w')

    chunk_name = '{name}_{id}.chunk'.format(name=slice_name,
                                            id='{id}')
    chunks_number = int(math.ceil(len(slices) / chunk_size));

    if binary:
        f.write('{width} {height} 0 {chunks} {slices}\n'.format(width=width,
                                                     height=height,
                                                     slices=len(slices),
                                                     chunks=chunks_number))
    else:
        f.write('{width} {height} {slices}\n'.format(width=width,
                                                     height=height,
                                                     slices=len(slices)))

    index_f = None
    if generate_index_file:
        index_f = open(os.path.join(output_directory, 'index.idx.xml'), 'w')
        index_f.write('<?xml version="1.0" encoding="UTF-8"?>\n<directory>\n')
        index_f.write('\t<file><name>{0}</name></file>\n'.format(info_name))

    if binary:
        for i in range(0, chunks_number):
            chunk_file_name = chunk_name.format(id=i)
            f.write('{id} {chunk}\n'.format(id=i,
                                            chunk=chunk_file_name))
            index_f.write('\t<file><name>{0}</name></file>\n'.format(chunk_file_name))


    slice_id = 0
    chunk_id = -1
    chunk_file_out = None

    for s in slices:
        cur_chunk_id = slice_id // chunk_size
        if binary and cur_chunk_id != chunk_id:
            chunk_id = cur_chunk_id
            if chunk_file_out is not None:
                chunk_file_out.close()
            chunk_file_name = chunk_name.format(id=chunk_id)
            chunk_file_out = open(os.path.join(output_directory, chunk_file_name), 'wb')
        slice_id += 1

        cropped = image.clone()
        cropped.crop(s.x,
                     s.y,
                     width=s.width,
                     height=s.height)
        cropped.compression_quality = int(compression_quality)
        print('Saving: {0}'.format(s.output_name))
        output_slice_name = os.path.join(output_directory, s.output_name)
        cropped.save(filename=output_slice_name)

        if binary:
            position = chunk_file_out.tell()
            size = 0

            slice_file = open(output_slice_name, mode='rb')
            chunk_file_out.write(slice_file.read())
            slice_file.close()

            size = chunk_file_out.tell() - position

            f.write('{x} {y} {width} {height} {chunk} {position} {length}\n'.format(
                x=s.x, y=s.y, width=s.width, height=s.height,
                chunk=chunk_id, position=position, length=size
            ))
            os.remove(output_slice_name)

        else:
            f.write('{x} {y} {width} {height} {name}\n'.format(
                x=s.x, y=s.y, width=s.width, height=s.height,
                name=s.output_name
            ))
            if generate_index_file:
                index_f.write('\t<file><name>{0}</name></file>\n'.format(s.output_name))

    if generate_index_file:
        index_f.write('</directory>\n')

try:
    parser = OptionParser()
    parser.add_option("-s", "--source", dest="source_image",
                      help="Image which should be divided into slices")
    parser.add_option("-p", "--slice-size",
                      dest="slice_size", type="int",
                      help="The max size of each slice")
    parser.add_option("-o", "--output-name",
                      dest="output_name",
                      help="The name of output")
    parser.add_option("-d", "--output-directory",
                      dest="output_dir",
                      default=".",
                      help="The name of dir to put everything")
    parser.add_option("-i", "--index",
                      dest="index",
                      action="store_true",
                      default=False,
                      help="Generate index for Resource Compiler")
    parser.add_option("-b", "--binary",
                      dest="binary",
                      action="store_true",
                      default=False,
                      help="Binary packed output")
    parser.add_option("-c", "--chunk",
                      dest="chunk",
                      type="int",
                      default=10,
                      help="Slices in one chunk")
    parser.add_option("-f", "--format",
                      dest="format",
                      default="jpg",
                      help="Format of the output: jpg, png, etc.")
    parser.add_option("-q", "--quality",
                      dest="quality",
                      default=100,
                      type="int",
                      help="Output quality [0, 100] for jpg")

    (options, args) = parser.parse_args()
    if options.output_name is None or options.source_image is None or options.slice_size is None:
        parser.print_help()
    else:
        sliceImage(options.source_image,
                   slice_size=options.slice_size,
                   slice_name=options.output_name,
                   output_directory=options.output_dir,
                   slice_format=options.format,
                   compression_quality=options.quality,
                   generate_index_file=options.index,
                   binary=options.binary,
                   chunk_size=options.chunk)
except Exception as e:
    print(e.__doc__, file=sys.stderr)
    print(e.__str__(), file=sys.stderr)
    sys.exit(errno.EIO)
