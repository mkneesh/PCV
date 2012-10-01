import os
import fnmatch
import getopt
import sys
import pickle

import PCV.localdescriptors.sift as sift
import PCV.imagesearch.vocabulary as vocabulary


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


def generate_vocab(in_sift_dir, out_pickle_dir, subsampling=10):
    if not os.path.exists(out_pickle_dir):
        os.makedirs(out_pickle_dir)
    o = os.path.join(out_pickle_dir, 'vocabulary.pkl')

    sift_files = [f for f in matching_files(in_sift_dir, pattern="*.sift")]
    voc = vocabulary.Vocabulary('ukbenchtest')
    print 'Generating vocabulary from:%s into:%s' % (in_sift_dir, o)
    voc.train(sift_files, len(sift_files), subsampling)

    with open(o, 'wb') as f:
        pickle.dump(voc, f)
    print 'Generated vocab name:%s size:%s' % (voc.name, voc.nbr_words)

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
        if action == 'VOC':
            in_dir = opts.get('--input') or opts.get('-i')
            out_dir = opts.get('--output') or opts.get('-o')
            print 'Generating vocab from:%s and storing in:%s' % (in_dir, out_dir)
            generate_vocab(in_dir, out_dir)
