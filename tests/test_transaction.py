import unittest
from unittest.mock import patch, MagicMock
from collections import OrderedDict
import binascii

from src.transactions import Transaction


class TestTransaction(unittest.TestCase):

    def setUp(self):
        # Sample data for testing
        self.sender_address = 'sender_address_123'
        self.sender_private_key = '73656e6465725f707269766174655f6b65795f686578'  # hex-encoded
        self.recipient_address = 'recipient_address_456'
        self.value = 100

        self.transaction = Transaction(
            self.sender_address,
            self.sender_private_key,
            self.recipient_address,
            self.value
        )

    def test_init(self):
        # Test initialization
        self.assertEqual(self.transaction.sender_address, self.sender_address)
        self.assertEqual(self.transaction.sender_private_key,
                         self.sender_private_key)
        self.assertEqual(self.transaction.recipient_address,
                         self.recipient_address)
        self.assertEqual(self.transaction.value, self.value)

    def test_to_dict(self):
        # Test the to_dict method
        expected_dict = OrderedDict({
            'sender_address': self.sender_address,
            'recipient_address': self.recipient_address,
            'value': self.value
        })
        self.assertEqual(self.transaction.to_dict(), expected_dict)

    @patch('src.transactions.RSA.importKey')  # Mock the private key
    @patch('src.transactions.PKCS1_v1_5.new')  # Mock the signer
    def test_sign_transaction(self, mock_pkcs1, mock_import_key):
        # Mock the private key import
        mock_private_key = MagicMock()
        mock_import_key.return_value = mock_private_key

        # Mock the signer object and the signing process
        mock_signer = MagicMock()
        mock_pkcs1.return_value = mock_signer

        # Mock the signature
        mock_signature = b'signed_data'
        mock_signer.sign.return_value = mock_signature

        # Call sign_transaction and verify the result
        signature = self.transaction.sign_transaction()
        self.assertEqual(signature, binascii.hexlify(
            mock_signature).decode('ascii'))

        # Check that importKey and sign were called with the correct parameters
        mock_import_key.assert_called_once_with(
            binascii.unhexlify(self.sender_private_key))
        mock_signer.sign.assert_called_once()


if __name__ == '__main__':
    unittest.main()
