import os
import shutil
import fnmatch
import getopt
import sys
import pickle

import PCV.localdescriptors.sift as sift
import PCV.imagesearch.vocabulary as vocabulary
import PCV.imagesearch.imagesearch as imagesearch


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


def _get_dirs(in_dir):
    image_dir = os.path.join(in_dir, "images")
    sift_dir = os.path.join(in_dir, "sift")
    voc_dir = os.path.join(in_dir, "voc")
    db_dir = os.path.join(in_dir, "db")
    return {'images': image_dir, 'sift': sift_dir, 'voc': voc_dir, 'db': db_dir}


def _to_sift_file(image_file):
    name_no_ext = os.path.splitext(image_file)[0]
    return ''.join([name_no_ext, '.sift'])


def _db_path(dirs):
    return os.path.join(dirs['db'], 'tests.db')


def _voc_path(dirs):
    return os.path.join(dirs['voc'], 'vocabulary.pkl')


def generate_sift(image_dir, dirs, image_pattern="*.jpg", max_=1000, copy_images=True):
    for i, f in enumerate(matching_files(image_dir)):
        o = os.path.join(dirs['sift'], _to_sift_file(os.path.basename(f)))
        print '%s of %s) Processing:%s' % (i, max_, f)
        sift.process_image(f, o)
        if copy_images:
            img_dstn = os.path.join(dirs['images'], os.path.basename(f))
            shutil.copyfile(f, img_dstn)
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


def index_files(dirs):
    print 'Loading files'
    voc = _load_voc(dirs)
    db = _db_path(dirs)
    indx = imagesearch.Indexer(db, voc)

    for img_file in matching_files(dirs['images']):
        img_file_name = os.path.basename(img_file)
        sift_file = os.path.join(dirs['sift'], _to_sift_file(img_file_name))
        locs, descr = sift.read_features_from_file(sift_file)
        print 'Adding img_file:%s to index' % (img_file_name)
        indx.add_to_index(img_file_name, descr)
    indx.db_commit()


def query_image(dirs, img_file):
    db = _db_path(dirs)
    src = imagesearch.Searcher(db, _load_voc(dirs))
    f = os.path.basename(img_file)
    print 'Searching for:%s' % img_file
    print src.query(f)


def db_info(dirs):
    indx = imagesearch.Indexer(_db_path(dirs), None)
    con = indx.con
    print 'Num images indexed:%s' % con.execute('select count(filename) from imlist').fetchone()
    print con.execute('select * from imlist').fetchone()


def _load_voc(dirs):
    with open(_voc_path(dirs), 'rb') as f:
        voc = pickle.load(f)
    return voc

if __name__ == '__main__':
    opts = dict(getopt.getopt(sys.argv[1:], "a:b:i:o:m:", ["action=", "base=", "input=", "output=", "max="])[0])
    if opts:
        action = opts.get('--action')
        base_dir = opts.get('--base') or opts.get('-b')

        dirs = _get_dirs(base_dir)
        for d in dirs.values():
            if not os.path.exists(d):
                os.makedirs(d)

        if action == "INIT":
            db = _db_path(dirs)
            print 'Creating tables:%s' % db
            imagesearch.Indexer(db, None).create_tables()
            print 'Done creating tables'
        if action == 'SIFT':
            in_dir = opts.get('--input') or opts.get('-i')
            max_ = opts.get('--max') or opts.get('-m')
            print 'Max:%s Generating sift-features from:%s to:%s' % (max_, in_dir, dirs['sift'])
            generate_sift(in_dir, dirs, max_=int(max_), copy_images=True)
        if action == 'VOC':
            print 'Generating vocab from:%s and storing in:%s' % (dirs['sift'], dirs['voc'])
            generate_vocab(dirs['sift'], dirs['voc'])
        if action == "INDEX":
            print 'Creating index:%s' % dirs['db']
            index_files(dirs)
        if action == "QUERY":
            image_file = opts.get('--input') or opts.get('-i')
            dirs = _get_dirs(base_dir)
            print 'Searching for image:%s' % image_file
            query_image(dirs, image_file)
        if action == "DB_INFO":
            db_info(dirs)
