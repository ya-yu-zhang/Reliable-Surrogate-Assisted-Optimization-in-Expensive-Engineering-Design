"""Certificate semantics and information-use tests, not engineering samples."""
from fractions import Fraction as F
import unittest
from src.h1_certificate_routing import no_better_certificate


class CertificateRoutingTests(unittest.TestCase):
    def test_failed_pending_cap_never_calls_reader(self):
        def forbidden():self.fail('Unnecessary action-set reader called')
        r=no_better_certificate(F(100),F(90),F(1),F(0),forbidden)
        self.assertFalse(r['certified']);self.assertFalse(r['action_set_reader_called'])

    def test_closed_threshold_equality_requires_next_bound(self):
        calls=[]
        def reader():calls.append(1);return F(90)
        r=no_better_certificate(F(100),F(90),F(90),F(0),reader)
        self.assertTrue(r['certified']);self.assertEqual(calls,[1])

    def test_stronger_response_domain_changes_cap(self):
        r=no_better_certificate(F(100),F(90),F(1),F(95),lambda:F(92))
        self.assertTrue(r['certified']);self.assertTrue(r['action_set_reader_called'])

    def test_next_bound_still_blocks_certificate(self):
        r=no_better_certificate(F(100),F(90),F(95),F(0),lambda:F(89))
        self.assertFalse(r['certified']);self.assertTrue(r['action_set_reader_called'])
