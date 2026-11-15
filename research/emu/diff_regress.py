"""Sessions that once differed from the ROM: they must all agree now.   python diff_regress.py"""
from functools import partial
from multiprocessing import Pool
from diff_machine import session
SEEDS = [103, 104, 106, 107, 109, 111, 113, 117, 118, 121, 123, 124, 125, 127, 128, 129, 136, 139, 143, 146, 148, 152,
         156, 157, 159, 161, 163, 172, 174, 176, 177, 179, 201, 202, 223, 225, 243, 319, 341, 344, 356, 406, 522, 552]
if __name__ == '__main__':
    with Pool(2) as p:
        bad = sum(r is not None for r in p.imap(partial(session, nkeys=70), SEEDS))
    print('%d sessions that once differed: %d still differ' % (len(SEEDS), bad))
