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

        # Send POST request to the /wallet/new route
        response = self.client.post('/wallet/new')

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
        self.assertEqual(wallets[response_json['public_key']]['balance'], 0.0)

        # Ensure that the appropriate methods were called
        mock_rsa_generate.assert_called_once_with(3072, mock_random_gen)
        mock_private_key.publickey.assert_called_once()
        mock_private_key.exportKey.assert_called_once_with(format='DER')
        mock_public_key.exportKey.assert_called_once_with(format='DER')

    # Patch the wallets dictionary with an empty dictionary
    @patch.dict('src.app.routes.wallets', {}, clear=True)
    # Mock balance calculation
    @patch('src.app.routes.blockchain.get_available_balance')
    # Mock transaction submission
    @patch('src.app.routes.blockchain.submit_transaction')
    def test_new_transaction(self, mock_submit_transaction, mock_get_available_balance):
        # Set up wallets with balances
        from src.app.routes import wallets  # Import wallets after patching
        wallets['sender_address_123'] = {
            'private_key': 'private_key_abc123', 'balance': 200.0}
        wallets['recipient_address_456'] = {
            'private_key': 'private_key_xyz456', 'balance': 50.0}

        # Mock JSON data for the POST request
        json_data = {
            'sender_address': 'sender_address_123',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'recipient_address_456',
            'amount': 100.0
        }

        # Mock balance check to return enough balance
        mock_get_available_balance.return_value = 200.0

        # Mock transaction submission success
        mock_submit_transaction.return_value = 1

        # Send POST request to /transactions/new route with JSON data
        response = self.client.post('/transactions/new', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_json['message'],
                         'Transaction will be added to Block 1')

        # Ensure that the balance was checked correctly
        mock_get_available_balance.assert_called_once_with(
            address='sender_address_123')

        # Ensure that the submit_transaction method was called correctly
        mock_submit_transaction.assert_called_once_with(
            'sender_address_123',
            'private_key_abc123',
            'recipient_address_456',
            100.0
        )

    @patch.dict('src.app.routes.wallets', {}, clear=True)
    @patch('src.app.routes.blockchain.get_available_balance')
    @patch('src.app.routes.blockchain.submit_transaction')
    def test_new_transaction_missing_fields(self, mock_submit_transaction, mock_get_available_balance):
        # Test missing fields
        json_data = {
            'sender_address': 'sender_address_123',
            'recipient_address': 'recipient_address_456',
            # 'amount' and 'sender_private_key' are missing
        }

        # Send POST request with missing fields
        response = self.client.post('/transactions/new', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response_json)
        self.assertEqual(response_json['error'], 'Missing required field: sender_private_key')

    @patch.dict('src.app.routes.wallets', {}, clear=True)
    @patch('src.app.routes.blockchain.get_available_balance')
    @patch('src.app.routes.blockchain.submit_transaction')
    def test_new_transaction_invalid_amount(self, mock_submit_transaction, mock_get_available_balance):
        # Test invalid amount
        json_data = {
            'sender_address': 'sender_address_123',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'recipient_address_456',
            'amount': 'invalid_amount'  # Invalid non-numeric amount
        }

        # Send POST request with invalid amount
        response = self.client.post('/transactions/new', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response_json)
        self.assertEqual(response_json['error'], 'Amount must be a number.')

    @patch.dict('src.app.routes.wallets', {}, clear=True)
    @patch('src.app.routes.blockchain.get_available_balance')
    def test_new_transaction_insufficient_balance(self, mock_get_available_balance):
        # Set up wallets with low balance for the sender
        from src.app.routes import wallets  # Import wallets after patching
        wallets['sender_address_123'] = {
            'private_key': 'private_key_abc123', 'balance': 50.0}
        wallets['recipient_address_456'] = {
            'private_key': 'private_key_xyz456', 'balance': 50.0}

        # Mock JSON data for the POST request
        json_data = {
            'sender_address': 'sender_address_123',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'recipient_address_456',
            'amount': 100.0  # More than sender's balance
        }

        # Mock balance check to return insufficient balance
        mock_get_available_balance.return_value = 50.0

        # Send POST request to /transactions/new route with JSON data
        response = self.client.post('/transactions/new', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['error'], 'Insufficient balance.')

        # Ensure the balance check was performed
        mock_get_available_balance.assert_called_once_with(
            address='sender_address_123')

    @patch.dict('src.app.routes.wallets', {}, clear=True)
    def test_new_transaction_sender_address_not_exist(self):
        # Set up only the recipient wallet
        from src.app.routes import wallets  # Import wallets after patching
        wallets['recipient_address_456'] = {
            'private_key': 'private_key_xyz456', 'balance': 50.0}

        # Mock JSON data for the POST request
        json_data = {
            'sender_address': 'non_existent_sender',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'recipient_address_456',
            'amount': 100.0
        }

        # Send POST request to /transactions/new route with JSON data
        response = self.client.post('/transactions/new', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['error'],
                         'Sender address does not exist.')

    @patch.dict('src.app.routes.wallets', {}, clear=True)
    def test_new_transaction_recipient_address_not_exist(self):
        # Set up only the sender wallet
        from src.app.routes import wallets  # Import wallets after patching
        wallets['sender_address_123'] = {
            'private_key': 'private_key_abc123', 'balance': 200.0}

        # Mock JSON data for the POST request
        json_data = {
            'sender_address': 'sender_address_123',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'non_existent_recipient',
            'amount': 100.0
        }

        # Send POST request to /transactions/new route with JSON data
        response = self.client.post('/transactions/new', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response_json['error'],
                         'Recipient address does not exist.')

    @patch.dict('src.app.routes.wallets', {}, clear=True)
    @patch('src.app.routes.blockchain.get_available_balance')
    @patch('src.app.routes.blockchain.submit_transaction')
    def test_new_transaction_invalid_transaction(self, mock_submit_transaction, mock_get_available_balance):
        # Set up wallets with balances
        from src.app.routes import wallets  # Import wallets after patching
        wallets['sender_address_123'] = {
            'private_key': 'private_key_abc123', 'balance': 200.0}
        wallets['recipient_address_456'] = {
            'private_key': 'private_key_xyz456', 'balance': 50.0}

        # Mock balance check to return enough balance
        mock_get_available_balance.return_value = 200.0

        # Mock transaction submission to return None (indicating invalid transaction)
        mock_submit_transaction.return_value = None

        # Mock JSON data for the POST request
        json_data = {
            'sender_address': 'sender_address_123',
            'sender_private_key': 'private_key_abc123',
            'recipient_address': 'recipient_address_456',
            'amount': 100.0
        }

        # Send POST request to /transactions/new route with JSON data
        response = self.client.post('/transactions/new', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 406)
        self.assertIn('message', response_json)
        self.assertEqual(response_json['message'], 'Invalid Transaction!')

    @patch.dict('src.app.routes.wallets', {}, clear=True)
    @patch('src.app.routes.blockchain.proof_of_work')
    @patch('src.app.routes.blockchain.create_block')
    @patch('src.app.routes.blockchain.submit_transaction')
    def test_mine(self, mock_submit_transaction, mock_create_block, mock_proof_of_work):
        # Set up wallet for the miner
        from src.app.routes import wallets, blockchain  # Import wallets after patching
        wallets['miner_address_123'] = {
            'private_key': 'private_key_abc123', 'balance': 0.0}

        # Mock JSON data for the POST request
        json_data = {
            'miner_address': 'miner_address_123'
        }

        # Mock the proof_of_work and create_block methods
        mock_proof_of_work.return_value = 123  # Mocked nonce
        # Capture the real previous hash
        previous_hash = blockchain.hash(blockchain.chain[-1])
        mock_create_block.return_value = {
            'block_number': 2,
            'transactions': [],
            'nonce': 123,
            'previous_hash': previous_hash
        }

        # Mock the transaction submission
        mock_submit_transaction.return_value = True

        # Send POST request to /mine route with JSON data
        response = self.client.post('/mine', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json['message'], 'New Block Forged')
        self.assertEqual(response_json['block_number'], 2)

        # Ensure the submit_transaction method was called for the mining reward
        mock_submit_transaction.assert_called_once_with(
            sender_address='THE BLOCKCHAIN',
            sender_private_key=None,
            recipient_address='miner_address_123',
            value=1
        )

        # Ensure the proof_of_work and create_block methods were called
        mock_proof_of_work.assert_called_once()
        mock_create_block.assert_called_once_with(123, previous_hash)

    @patch.dict('src.app.routes.wallets', {}, clear=True)
    @patch('src.app.routes.blockchain.proof_of_work')
    @patch('src.app.routes.blockchain.create_block')
    @patch('src.app.routes.blockchain.submit_transaction')
    def test_mine_missing_miner_address(self, mock_submit_transaction, mock_create_block, mock_proof_of_work):
        # Test missing miner_address in the JSON payload
        json_data = {}  # No miner_address provided

        # Send POST request to /mine route with missing miner_address
        response = self.client.post('/mine', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response_json)
        self.assertEqual(response_json['error'], 'Missing required field: miner_address')

    def test_register_node(self):
        # Mock JSON data for the POST request
        json_data = {
            'nodes': ['http://localhost:5001', 'http://localhost:5002']
        }

        # Simulate POST request to register new nodes
        response = self.client.post('/nodes/register', json=json_data)

        # Validate the response status code and content
        self.assertEqual(response.status_code, 201)
        response_json = response.get_json()
        self.assertIn('total_nodes', response_json)
        self.assertEqual(len(response_json['total_nodes']), 2)

    @patch('src.app.routes.blockchain.register_node')  # Mock the register_node method
    def test_register_nodes_missing_field(self, mock_register_node):
        # Test when 'nodes' field is missing in the JSON payload
        json_data = {}  # No 'nodes' field provided

        # Send POST request to /nodes/register route with missing 'nodes'
        response = self.client.post('/nodes/register', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response_json)
        self.assertEqual(response_json['error'], 'Missing or invalid required field: nodes (must be a non-empty list)')

    @patch('src.app.routes.blockchain.register_node')  # Mock the register_node method
    def test_register_nodes_invalid_field_type(self, mock_register_node):
        # Test when 'nodes' field is not a list
        json_data = {
            'nodes': 'not_a_list'  # Invalid type
        }

        # Send POST request to /nodes/register route with invalid 'nodes' field type
        response = self.client.post('/nodes/register', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response_json)
        self.assertEqual(response_json['error'], 'Missing or invalid required field: nodes (must be a non-empty list)')

    @patch('src.app.routes.blockchain.register_node')  # Mock the register_node method
    def test_register_nodes_empty_list(self, mock_register_node):
        # Test when 'nodes' field is an empty list
        json_data = {
            'nodes': []  # Empty list
        }

        # Send POST request to /nodes/register route with empty 'nodes' field
        response = self.client.post('/nodes/register', json=json_data)

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and error message
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response_json)
        self.assertEqual(response_json['error'], 'Missing or invalid required field: nodes (must be a non-empty list)')

    @patch('src.app.routes.blockchain.resolve_conflicts')
    def test_resolve_conflicts(self, mock_resolve_conflicts):
        # Mock the resolve_conflicts method to return True (indicating the chain was replaced)
        mock_resolve_conflicts.return_value = True

        # Simulate GET request to resolve node conflicts
        response = self.client.get('/nodes/resolve')

        # Validate the response
        self.assertEqual(response.status_code, 200)
        response_json = response.get_json()
        self.assertIn('message', response_json)
        self.assertIn('new_chain', response_json)
        self.assertEqual(response_json['message'], 'Our chain was replaced')

    @patch('src.app.routes.blockchain.resolve_conflicts')  # Mock resolve_conflicts method
    @patch('src.app.routes.blockchain.chain', new_callable=list)  # Mock blockchain.chain
    def test_consensus_authoritative_chain(self, mock_chain, mock_resolve_conflicts):
        # Simulate the chain being authoritative (not replaced)
        mock_resolve_conflicts.return_value = False

        # Simulate a blockchain with a few blocks
        mock_chain.extend([
            {
                'block_number': 1,
                'transactions': [],
                'nonce': 1234,
                'previous_hash': 'abcd1234'
            },
            {
                'block_number': 2,
                'transactions': [{'sender': 'sender_1', 'recipient': 'recipient_1', 'amount': 50.0}],
                'nonce': 5678,
                'previous_hash': 'abcd5678'
            }
        ])

        # Send GET request to /nodes/resolve route
        response = self.client.get('/nodes/resolve')

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response_json)
        self.assertEqual(response_json['message'], 'Our chain is authoritative')

        # Check that the chain is returned correctly in the response
        self.assertIn('chain', response_json)
        self.assertEqual(len(response_json['chain']), 2)
        self.assertEqual(response_json['chain'][0]['block_number'], 1)
        self.assertEqual(response_json['chain'][1]['block_number'], 2)

    @patch('src.app.routes.blockchain.nodes', new_callable=set)
    def test_get_nodes(self, mock_nodes):
        # Simulate some nodes in the blockchain
        mock_nodes.update({'http://localhost:5001', 'http://localhost:5002'})

        # Send GET request to /nodes/get route
        response = self.client.get('/nodes/get')

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertIn('nodes', response_json)
        self.assertEqual(len(response_json['nodes']), 2)
        self.assertIn('http://localhost:5001', response_json['nodes'])
        self.assertIn('http://localhost:5002', response_json['nodes'])

    @patch('src.app.routes.blockchain.nodes', new_callable=set)
    def test_get_nodes_empty(self, mock_nodes):
        # Simulate an empty set of nodes
        mock_nodes.clear()

        # Send GET request to /nodes/get route
        response = self.client.get('/nodes/get')

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertIn('nodes', response_json)
        self.assertEqual(len(response_json['nodes']), 0)  # No nodes in the blockchain

    @patch('src.app.routes.blockchain.transactions', new_callable=list)
    def test_get_transactions(self, mock_transactions):
        # Simulate some transactions in the blockchain
        mock_transactions.extend([
            {'sender': 'sender_1', 'recipient': 'recipient_1', 'amount': 50.0},
            {'sender': 'sender_2', 'recipient': 'recipient_2', 'amount': 100.0}
        ])

        # Send GET request to /transactions/get route
        response = self.client.get('/transactions/get')

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertIn('transactions', response_json)
        self.assertEqual(len(response_json['transactions']), 2)

        # Validate transaction details
        self.assertEqual(response_json['transactions'][0]['sender'], 'sender_1')
        self.assertEqual(response_json['transactions'][0]['recipient'], 'recipient_1')
        self.assertEqual(response_json['transactions'][0]['amount'], 50.0)

        self.assertEqual(response_json['transactions'][1]['sender'], 'sender_2')
        self.assertEqual(response_json['transactions'][1]['recipient'], 'recipient_2')
        self.assertEqual(response_json['transactions'][1]['amount'], 100.0)

    @patch('src.app.routes.blockchain.transactions', new_callable=list)
    def test_get_transactions_empty(self, mock_transactions):
        # Simulate no transactions in the blockchain
        mock_transactions.clear()

        # Send GET request to /transactions/get route
        response = self.client.get('/transactions/get')

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertIn('transactions', response_json)
        self.assertEqual(len(response_json['transactions']), 0)  # No transactions in the pool

    @patch('src.app.routes.blockchain.chain', new_callable=list)
    def test_full_chain(self, mock_chain):
        # Simulate a blockchain with a few blocks
        mock_chain.extend([
            {
                'block_number': 1,
                'transactions': [],
                'nonce': 1234,
                'previous_hash': 'abcd1234'
            },
            {
                'block_number': 2,
                'transactions': [{'sender': 'sender_1', 'recipient': 'recipient_1', 'amount': 50.0}],
                'nonce': 5678,
                'previous_hash': 'abcd5678'
            }
        ])

        # Send GET request to /chain route
        response = self.client.get('/chain')

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertIn('chain', response_json)
        self.assertEqual(len(response_json['chain']), 2)
        self.assertEqual(response_json['length'], 2)

        # Validate block details
        self.assertEqual(response_json['chain'][0]['block_number'], 1)
        self.assertEqual(response_json['chain'][1]['block_number'], 2)
        self.assertEqual(response_json['chain'][1]['transactions'][0]['sender'], 'sender_1')

    @patch('src.app.routes.blockchain.chain', new_callable=list)
    def test_full_chain_empty(self, mock_chain):
        # Simulate an empty blockchain
        mock_chain.clear()

        # Send GET request to /chain route
        response = self.client.get('/chain')

        # Parse the JSON response
        response_json = response.get_json()

        # Validate the response status code and content
        self.assertEqual(response.status_code, 200)
        self.assertIn('chain', response_json)
        self.assertEqual(len(response_json['chain']), 0)
        self.assertEqual(response_json['length'], 0)

    def test_swagger_ui(self):
        # Test the Swagger UI route and follow redirects
        response = self.client.get('/swagger', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"<title>ChainAlchemy API Documentation</title>", response.data)

if __name__ == '__main__':
    unittest.main()
