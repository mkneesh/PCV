import os
import fnmatch
import getopt
import sys

import PCV.localdescriptors.sift as sift


def matching_files(in_dir, pattern="*.jpg"):
    for root, dirs, files in os.walk(in_dir):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                yield os.path.join(root, basename)


def load_images(path, max_=1000):
    images = []
    for i, f in enumerate(matching_files(path)):
        images.append(f)
        if max_ and max_ <= i:
            return images


def generate_sift(image_dir, sift_dir, image_pattern="*.jpg", max_=1000):
    if not os.path.exists(sift_dir):
        os.makedirs(sift_dir)

    for i, f in enumerate(matching_files(image_dir)):
        o = os.path.join(sift_dir, os.path.basename(f).replace(image_pattern[1:], '.sift'))
        print '%s of %s) Processing:%s' % (i, max_, f)
        sift.process_image(f, o)
        if max_ and i >= max_:
            return


def generate_vocab(in_dir, out_dir):
    pass

if __name__ == '__main__':
    opts = dict(getopt.getopt(sys.argv[1:], "a:i:o:m:", ["action=", "input=", "output=", "max="])[0])
    if opts:
        action = opts.get('--action')
        if action == 'SIFT':
            in_dir = opts.get('--input') or opts.get('-i')
            out_dir = opts.get('--output') or opts.get('-o')
            max_ = opts.get('--max') or opts.get('-m')
            print 'Max:%s Generating sift-features from:%s to:%s' % (max_, in_dir, out_dir)
            generate_sift(in_dir, out_dir, max_=int(max_))
        if action == 'GENVOC':
            in_dir = opts.get('--input') or opts.get('-i')
            out_dir = opts.get('--output') or opts.get('-o')
            print 'Generating vocab from:%s and storing in:%s' % (in_dir, out_dir)
            generate_vocab(in_dir, out_dir)
