# -*- coding: utf-8 -*-
import unittest
import os

import dotdot
import fake_env

from pubs import content, filebroker, databroker, datacache

import str_fixtures
from pubs import endecoder


class TestDataBroker(unittest.TestCase):

    def test_databroker(self):

        ende = endecoder.EnDecoder()
        page99_metadata = ende.decode_metadata(str_fixtures.metadata_raw0)
        page99_bibdata  = ende.decode_bibdata(str_fixtures.bibtex_raw0)

        for db_class in [databroker.DataBroker, datacache.DataCache]:
            self.fs = fake_env.create_fake_fs([content, filebroker])

            db = db_class('tmp', create=True)

            db.push_metadata('citekey1', page99_metadata)
            self.assertFalse(db.exists('citekey1', meta_check=True))
            self.assertFalse(db.exists('citekey1', meta_check=False))

            db.push_bibdata('citekey1', page99_bibdata)
            self.assertTrue(db.exists('citekey1', meta_check=False))
            self.assertTrue(db.exists('citekey1', meta_check=True))

            self.assertEqual(db.pull_metadata('citekey1'), page99_metadata)
            pulled = db.pull_bibdata('citekey1')['Page99']
            for key, value in pulled.items():
                self.assertEqual(pulled[key], page99_bibdata['Page99'][key])
            self.assertEqual(db.pull_bibdata('citekey1'), page99_bibdata)

            fake_env.unset_fake_fs([content, filebroker])

    def test_existing_data(self):

        ende = endecoder.EnDecoder()
        page99_bibdata  = ende.decode_bibdata(str_fixtures.bibtex_raw0)

        for db_class in [databroker.DataBroker, datacache.DataCache]:
            self.fs = fake_env.create_fake_fs([content, filebroker])
            fake_env.copy_dir(self.fs, os.path.join(os.path.dirname(__file__), 'testrepo'), 'repo')

            db = db_class('repo', create=False)

            self.assertEqual(db.pull_bibdata('Page99'), page99_bibdata)

            for citekey in ['10.1371_journal.pone.0038236',
                            '10.1371journal.pone.0063400',
                            'journal0063400']:
                db.pull_bibdata(citekey)
                db.pull_metadata(citekey)

            with self.assertRaises(IOError):
                db.pull_bibdata('citekey')
            with self.assertRaises(IOError):
                db.pull_metadata('citekey')

            db.add_doc('Larry99', 'docsdir://Page99.pdf')
            self.assertTrue(content.check_file('repo/doc/Page99.pdf', fail=False))
            self.assertTrue(content.check_file('repo/doc/Larry99.pdf', fail=False))

            db.remove_doc('docsdir://Page99.pdf')

            fake_env.unset_fake_fs([content, filebroker])


if __name__ == '__main__':
    unittest.main()
