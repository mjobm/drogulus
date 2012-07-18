"""
Ensures the routing table (a binary tree used to link kbuckets with key ranges
in the DHT) works as expected.
"""
from drogulus.dht.routingtable import RoutingTable
from drogulus.dht.contact import Contact
from drogulus.dht.kbucket import KBucket, KBucketFull
import unittest

class TestRoutingTable(unittest.TestCase):
    """
    Ensures the RoutingTable class works as expected.
    """

    def testInit(self):
        """
        Ensures an object is created as expected.
        """
        parentNodeID = 'abc'
        r = RoutingTable(parentNodeID)
        # Ensure the initial kbucket is created.
        self.assertEqual(1, len(r._buckets))
        # Ensure the parent's node ID is stored.
        self.assertEqual(parentNodeID, r._parentNodeID)

    def test_kbucketIndex(self):
        """
        Ensures the expected index is returned.
        """
        parentNodeID = 'abc'
        r = RoutingTable(parentNodeID)
        # a simple test with only one kbucket in the routing table.
        test_key = 'abc123'
        expected_index = 0
        actual_index = r._kbucketIndex(test_key)
        self.assertEqual(expected_index, actual_index)
        # a more complex test with multiple kbuckets.
        r._splitBucket(0)
        split_point = (2**160)/2
        lower_key = split_point - 1
        higher_key = split_point + 1
        expected_lower_index = 0
        expected_higher_index = 1
        actual_lower_index = r._kbucketIndex(lower_key)
        actual_higher_index = r._kbucketIndex(higher_key)
        self.assertEqual(expected_lower_index, actual_lower_index)
        self.assertEqual(expected_higher_index, actual_higher_index)

    def test_randomKeyInBucketRange(self):
        """
        Ensures the returned key is within the expected bucket range.
        """
        parentNodeID = 'abc'
        r = RoutingTable(parentNodeID)
        rangeMin = 1
        rangeMax = 2
        bucket = KBucket(rangeMin, rangeMax)
        r._buckets[0] = bucket
        expected = 1
        actual = int(r._randomKeyInBucketRange(0).encode('hex'), 16)
        self.assertEqual(expected, actual)

    def test_splitBucket(self):
        """
        Ensures that the correct bucket is split in two and that the contacts
        are found in the right place.
        """
        parentNodeID = 'abc'
        r = RoutingTable(parentNodeID)
        rangeMin = 0
        rangeMax = 10
        bucket = KBucket(rangeMin, rangeMax)
        contact1 = Contact(2, "192.168.0.1", 9999, 0)
        bucket.addContact(contact1)
        contact2 = Contact(4, "192.168.0.2", 8888, 0)
        bucket.addContact(contact2)
        contact3 = Contact(6, "192.168.0.3", 8888, 0)
        bucket.addContact(contact3)
        contact4 = Contact(8, "192.168.0.4", 8888, 0)
        bucket.addContact(contact4)
        r._buckets[0] = bucket
        # Sanity check
        self.assertEqual(1, len(r._buckets))
        r._splitBucket(0)
        # Two buckets!
        self.assertEqual(2, len(r._buckets))
        bucket1 = r._buckets[0]
        bucket2 = r._buckets[1]
        # Ensure the right number of contacts are in each bucket in the correct
        # order (most recently added at the head of the list).
        self.assertEqual(2, len(bucket1._contacts))
        self.assertEqual(2, len(bucket2._contacts))
        self.assertEqual(contact1, bucket1._contacts[0])
        self.assertEqual(contact2, bucket1._contacts[1])
        self.assertEqual(contact3, bucket2._contacts[0])
        self.assertEqual(contact4, bucket2._contacts[1])
        # Split the new bucket again, ensuring that only the target bucket is
        # modified.
        r._splitBucket(1)
        self.assertEqual(3, len(r._buckets))
        bucket3 = r._buckets[2]
        # kbucket1 remains un-changed
        self.assertEqual(2, len(bucket1._contacts))
        # kbucket2 only contains the lower half of its original contacts.
        self.assertEqual(1, len(bucket2._contacts))
        self.assertEqual(contact3, bucket2._contacts[0])
        # kbucket3 now contains the upper half of the original contacts.
        self.assertEqual(1, len(bucket3._contacts))
        self.assertEqual(contact4, bucket3._contacts[0])
        # Split the bucket at position 0 and ensure the resulting buckets are
        # in the correct position with the correct content.
        r._splitBucket(0)
        self.assertEqual(4, len(r._buckets))
        bucket1, bucket2, bucket3, bucket4 = r._buckets
        self.assertEqual(1, len(bucket1._contacts))
        self.assertEqual(contact1, bucket1._contacts[0])
        self.assertEqual(1, len(bucket2._contacts))
        self.assertEqual(contact2, bucket2._contacts[0])
        self.assertEqual(1, len(bucket3._contacts))
        self.assertEqual(contact3, bucket3._contacts[0])
        self.assertEqual(1, len(bucket4._contacts))
        self.assertEqual(contact4, bucket4._contacts[0])

    def testAddContact(self):
        """
        Ensures that a newly discovered node in the network is added to the
        correct kbucket in the routing table.
        """
        parentNodeID = 'abc'
        r = RoutingTable(parentNodeID)