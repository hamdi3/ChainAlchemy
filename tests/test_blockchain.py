import os
import sys
import unittest
import binascii
from unittest.mock import MagicMock, patch
from uuid import uuid4
from Crypto.PublicKey import RSA
import requests

from src.blockchain import MINING_REWARD, Blockchain, MINING_SENDER  # Assuming you save your class in a file called blockchain.py


sys.path.insert(0, os.path.abspath(
    # to solve import issues in src
    os.path.join(os.path.dirname(__file__), '../src')))

class TestBlockchain(unittest.TestCase):

    def setUp(self):
        self.blockchain = Blockchain()
        self.private_key = RSA.generate(1024)
        self.public_key = self.private_key.publickey()
        self.sender_private_key = binascii.hexlify(self.private_key.exportKey(format='DER')).decode('ascii')
        self.sender_address = binascii.hexlify(self.public_key.exportKey(format='DER')).decode('ascii')
        self.recipient_address = str(uuid4()).replace('-', '')

    def test_register_node_valid(self):
        # Valid node registration
        self.blockchain.register_node('http://192.168.0.1:5000')
        self.assertIn('192.168.0.1:5000', self.blockchain.nodes)

    def test_register_node_invalid(self):
        # Invalid node URLs
        invalid_urls = [
            '????',
            '####',
        ]
        
        for url in invalid_urls:
            with self.assertRaises(ValueError):
                self.blockchain.register_node(url)

    def test_sign_transaction(self):
        transaction = {'sender_address': self.sender_address,
                       'recipient_address': self.recipient_address, 'value': 100}
        signature = self.blockchain.sign_transaction(
            self.sender_private_key, transaction)
        self.assertIsInstance(signature, str)
        self.assertTrue(len(signature) % 2 == 0)

    def test_verify_transaction_signature(self):
        transaction = {'sender_address': self.sender_address,
                       'recipient_address': self.recipient_address, 'value': 100}
        signature = self.blockchain.sign_transaction(
            self.sender_private_key, transaction)
        self.assertTrue(self.blockchain.verify_transaction_signature(
            self.sender_address, signature, transaction))

    def test_invalid_transaction_signature(self):
        transaction = {'sender_address': self.sender_address,
                       'recipient_address': self.recipient_address, 'value': 100}
        signature = self.blockchain.sign_transaction(
            self.sender_private_key, transaction)

        # Modify transaction data to invalidate the signature
        altered_transaction = {'sender_address': self.sender_address,
                               'recipient_address': self.recipient_address, 'value': 200}

        self.assertFalse(self.blockchain.verify_transaction_signature(
            self.sender_address, signature, altered_transaction))

    def test_submit_transaction(self):
        # Submit valid transaction
        block_index = self.blockchain.submit_transaction(
            self.sender_address, self.sender_private_key, self.recipient_address, 100)
        self.assertEqual(block_index, 2)

    def test_submit_invalid_transaction(self):
        # Invalid transaction (wrong signature)
        with self.assertRaises(ValueError):
            self.blockchain.submit_transaction(
                self.sender_address, 'invalid_private_key', self.recipient_address, 100)

    def test_get_balance(self):
        # Mining reward, expect no reduction in balance for the mining sender
        self.blockchain.submit_transaction(
            MINING_SENDER, None, self.recipient_address, MINING_REWARD)
        self.blockchain.create_block(nonce=1, previous_hash='abcd')

        balance = self.blockchain.get_balance(self.recipient_address)
        self.assertEqual(balance, MINING_REWARD)

    def test_get_available_balance(self):
        # Submit a mining reward transaction (add it to pending transactions)
        self.blockchain.submit_transaction(
            MINING_SENDER, None, self.recipient_address, MINING_REWARD)

        # Mine a block to confirm the mining reward transaction
        self.blockchain.create_block(nonce=12345, previous_hash='abcd')

        # Now, get the confirmed balance (after the mining reward transaction has been included in a block)
        confirmed_balance = self.blockchain.get_balance(self.recipient_address)

        # Assert that the confirmed balance is equal to the mining reward
        self.assertEqual(confirmed_balance, MINING_REWARD)

        # Submit a pending transaction to the recipient
        self.blockchain.submit_transaction(
            self.sender_address, self.sender_private_key, self.recipient_address, 50)

        # Available balance should be confirmed balance + pending transaction amount
        available_balance = self.blockchain.get_available_balance(self.recipient_address)

        # The available balance should now be the mining reward + 50
        self.assertEqual(available_balance, confirmed_balance + 50)


    def test_create_block(self):
        previous_block = self.blockchain.chain[-1]
        block = self.blockchain.create_block(nonce=12345, previous_hash='abcd')

        self.assertEqual(block['block_number'], 2)
        self.assertEqual(block['previous_hash'], 'abcd')
        self.assertEqual(len(block['transactions']), 0)  # Transactions list should be reset
        self.assertEqual(block['nonce'], 12345)

    def test_hash_block(self):
        block = self.blockchain.chain[-1]
        block_hash = self.blockchain.hash(block)
        self.assertEqual(len(block_hash), 64)  # SHA-256 hash length

    def test_proof_of_work(self):
        nonce = self.blockchain.proof_of_work()
        self.assertIsInstance(nonce, int)

    def test_valid_proof(self):
        # Test that valid_proof correctly identifies a valid hash
        last_block = self.blockchain.chain[-1]
        last_hash = self.blockchain.hash(last_block)
        nonce = self.blockchain.proof_of_work()

        self.assertTrue(self.blockchain.valid_proof(
            self.blockchain.transactions, last_hash, nonce))

    def test_invalid_proof(self):
        # Test that valid_proof correctly identifies an invalid hash
        self.assertFalse(self.blockchain.valid_proof(
            self.blockchain.transactions, 'abcd', 12345))

    def test_valid_chain(self):
        # Create the first block (genesis block is already created)
        previous_block = self.blockchain.chain[-1]
        previous_hash = self.blockchain.hash(previous_block)  # Correct previous hash
        nonce = self.blockchain.proof_of_work()  # Calculate valid nonce

        # Create a new block with valid nonce and previous hash
        self.blockchain.create_block(nonce=nonce, previous_hash=previous_hash)

        # Test if the blockchain is valid
        self.assertTrue(self.blockchain.valid_chain(self.blockchain.chain))


    def test_invalid_chain(self):
        # Submit a transaction to ensure the block has a transaction
        self.blockchain.submit_transaction(
            self.sender_address, self.sender_private_key, self.recipient_address, 100)

        # Create the first block (genesis block is already created)
        previous_block = self.blockchain.chain[-1]
        previous_hash = self.blockchain.hash(previous_block)
        nonce = self.blockchain.proof_of_work()

        # Create a new block that includes the transaction
        self.blockchain.create_block(nonce=nonce, previous_hash=previous_hash)

        # Tamper with the chain by modifying the value of the transaction
        self.blockchain.chain[1]['transactions'][0]['value'] = 999  # Tampering the chain

        # Test if the chain is invalid
        self.assertFalse(self.blockchain.valid_chain(self.blockchain.chain))


    def test_resolve_conflicts(self):
        # Create another blockchain instance with a longer chain
        other_blockchain = Blockchain()

        # Mine multiple blocks to make other_blockchain longer than the current blockchain
        for _ in range(2):  # Creating 2 more blocks to make it longer
            previous_block = other_blockchain.chain[-1]
            previous_hash = other_blockchain.hash(previous_block)
            nonce = other_blockchain.proof_of_work()
            other_blockchain.create_block(nonce=nonce, previous_hash=previous_hash)

        # Simulate adding a node and that node providing the other blockchain
        self.blockchain.nodes.add('localhost:5000')  # Simulate another node

        # Mock the requests.get to simulate returning the longer chain from the other node
        requests.get = unittest.mock.MagicMock(return_value=unittest.mock.Mock(
            status_code=200,
            json=lambda: {
                'length': len(other_blockchain.chain),
                'chain': other_blockchain.chain
            }
        ))

        # Now resolve conflicts; our blockchain should adopt the longer valid chain
        conflict_resolved = self.blockchain.resolve_conflicts()

        # Assert that the conflict was resolved (i.e., our chain was replaced by the longer one)
        self.assertTrue(conflict_resolved)

        # Assert that our blockchain's chain is now the same as the other blockchain's chain
        self.assertEqual(self.blockchain.chain, other_blockchain.chain)



if __name__ == '__main__':
    unittest.main()