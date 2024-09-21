import binascii
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from src.app import create_app

sys.path.insert(0, os.path.abspath(
    # to solve import issues in src
    os.path.join(os.path.dirname(__file__), '../src')))


class TestRoutes(unittest.TestCase):

    def setUp(self):
        # Set up Flask test client
        self.app = create_app()
        self.client = self.app.test_client()

    def test_home(self):
        # Simulate a request to the '/' route
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to Flask!', response.data)

    # Patch the wallets dictionary with an empty dictionary
    @patch.dict('src.app.routes.wallets', {}, clear=True)
    @patch('src.app.routes.RSA.generate')  # Mock RSA.generate
    @patch('src.app.routes.Crypto.Random.new')  # Mock Crypto.Random.new().read
    def test_new_wallet(self, mock_random_new, mock_rsa_generate):
        # Mocking the random generator
        mock_random_gen = MagicMock()
        mock_random_new.return_value.read = mock_random_gen

        # Mocking the private and public key generation
        mock_private_key = MagicMock()
        mock_public_key = MagicMock()
        mock_rsa_generate.return_value = mock_private_key
        mock_private_key.publickey.return_value = mock_public_key

        # Mocking the exportKey function for both private and public keys
        mock_private_key.exportKey.return_value = b'private_key_mock'
        mock_public_key.exportKey.return_value = b'public_key_mock'

        # Send GET request to the /wallet/new route
        response = self.client.get('/wallet/new')

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response_json['private_key'],
            binascii.hexlify(b'private_key_mock').decode('ascii')
        )
        self.assertEqual(
            response_json['public_key'],
            binascii.hexlify(b'public_key_mock').decode('ascii')
        )

        # Check that the new wallet is stored in the wallets dictionary (from the module)
        from src.app.routes import wallets  # Import wallets after patching
        self.assertIn(response_json['public_key'], wallets)
        self.assertEqual(wallets[response_json['public_key']]['private_key'],
                         response_json['private_key'])
        self.assertEqual(wallets[response_json['public_key']]['balance'], 100)

        # Ensure that the appropriate methods were called
        mock_rsa_generate.assert_called_once_with(1024, mock_random_gen)
        mock_private_key.publickey.assert_called_once()
        mock_private_key.exportKey.assert_called_once_with(format='DER')
        mock_public_key.exportKey.assert_called_once_with(format='DER')

    # Patch the wallets dictionary with an empty dictionary
    @patch.dict('src.app.routes.wallets', {}, clear=True)
    @patch('src.app.routes.Transaction')  # Mock the Transaction class
    def test_generate_transaction(self, mock_transaction):
        # Add mock wallets with initial balances
        from src.app.routes import wallets  # Import wallets after patching
        wallets['sender_address_123'] = {
            'private_key': 'private_key_abc123', 'balance': 200}
        wallets['recipient_address_456'] = {
            'private_key': 'private_key_xyz456', 'balance': 50}

        # Mock form data for the POST request
        form_data = {
            'sender_address': 'sender_address_123',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'recipient_address_456',
            'amount': 100
        }

        # Mock transaction instance and its methods
        mock_transaction_instance = MagicMock()
        mock_transaction.return_value = mock_transaction_instance

        # Mocking the to_dict and sign_transaction methods
        mock_transaction_instance.to_dict.return_value = {
            'sender_address': form_data['sender_address'],
            'recipient_address': form_data['recipient_address'],
            'value': int(form_data['amount'])
        }
        mock_transaction_instance.sign_transaction.return_value = 'mock_signature'

        # Send POST request to /generate/transaction route
        response = self.client.post('/generate/transaction', data=form_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json['transaction'], {
            'sender_address': form_data['sender_address'],
            'recipient_address': form_data['recipient_address'],
            'value': int(form_data['amount'])
        })
        self.assertEqual(response_json['signature'], 'mock_signature')

        # Ensure that the Transaction class was instantiated with the correct parameters
        mock_transaction.assert_called_once_with(
            form_data['sender_address'],
            form_data['sender_private_key'],
            form_data['recipient_address'],
            form_data['amount']
        )

        # Ensure that the to_dict and sign_transaction methods were called
        mock_transaction_instance.to_dict.assert_called_once()
        mock_transaction_instance.sign_transaction.assert_called_once()

        # Check that balances were updated correctly
        self.assertEqual(wallets['sender_address_123']
                         ['balance'], 100)  # 200 - 100
        self.assertEqual(wallets['recipient_address_456']
                         ['balance'], 150)  # 50 + 100

    # Patch the wallets dictionary with an empty dictionary
    @patch.dict('src.app.routes.wallets', {}, clear=True)
    def test_generate_transaction_insufficient_balance(self):
        # Add mock wallets with low balance for sender
        from src.app.routes import wallets  # Import wallets after patching
        wallets['sender_address_123'] = {
            'private_key': 'private_key_abc123', 'balance': 50}
        wallets['recipient_address_456'] = {
            'private_key': 'private_key_xyz456', 'balance': 50}

        # Mock form data for the POST request
        form_data = {
            'sender_address': 'sender_address_123',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'recipient_address_456',
            'amount': '100'  # More than sender's balance
        }

        # Send POST request to /generate/transaction route
        response = self.client.post('/generate/transaction', data=form_data)

        # Validate the response status code and content
        response_json = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['error'], 'Insufficient balance.')

    # Patch the wallets dictionary with an empty dictionary
    @patch.dict('src.app.routes.wallets', {}, clear=True)
    def test_generate_transaction_sender_address_not_exist(self):
        # Add a mock wallet for the recipient only
        from src.app.routes import wallets  # Import wallets after patching
        wallets['recipient_address_456'] = {
            'private_key': 'private_key_xyz456', 'balance': 50}

        # Mock form data for the POST request
        form_data = {
            'sender_address': 'non_existent_sender',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'recipient_address_456',
            'amount': '100'
        }

        # Send POST request to /generate/transaction route
        response = self.client.post('/generate/transaction', data=form_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['error'],
                         'Sender address does not exist.')

    # Patch the wallets dictionary with an empty dictionary
    @patch.dict('src.app.routes.wallets', {}, clear=True)
    def test_generate_transaction_recipient_address_not_exist(self):
        # Add a mock wallet for the sender only
        from src.app.routes import wallets  # Import wallets after patching
        wallets['sender_address_123'] = {
            'private_key': 'private_key_abc123', 'balance': 200}

        # Mock form data for the POST request
        form_data = {
            'sender_address': 'sender_address_123',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'non_existent_recipient',
            'amount': '100'
        }

        # Send POST request to /generate/transaction route
        response = self.client.post('/generate/transaction', data=form_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['error'],
                         'Recipient address does not exist.')


if __name__ == '__main__':
    unittest.main()
