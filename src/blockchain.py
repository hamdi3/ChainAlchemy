import binascii
import hashlib
import json
import requests
from time import time
from urllib.parse import urlparse
from uuid import uuid4
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from typing import OrderedDict

MINING_SENDER = "THE BLOCKCHAIN"
MINING_REWARD = 1.0
MINING_DIFFICULTY = 2


class Blockchain:

    def __init__(self):

        self.transactions = []
        self.chain = []
        self.nodes = set()
        # Generate random number to be used as node_id
        self.node_id = str(uuid4()).replace('-', '')
        # Create genesis block
        self.create_block(nonce=0, previous_hash='00')

    def register_node(self, node_url):
        """
        Add a new node to the list of nodes
        """
        # Checking node_url has valid format
        parsed_url = urlparse(url=node_url)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like '192.168.0.5:5000'.
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError('Invalid URL')

    def sign_transaction(self, sender_private_key, transaction):
        """
        Sign transaction with private key
        """
        private_key = RSA.importKey(
            binascii.unhexlify(sender_private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA256.new(str(transaction).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')

    def verify_transaction_signature(self, sender_address, signature, transaction):
        """
        Check that the provided signature corresponds to transaction
        signed by the public key (sender_address)
        """
        public_key = RSA.importKey(
            extern_key=binascii.unhexlify(sender_address))
        verifier = PKCS1_v1_5.new(rsa_key=public_key)
        h = SHA256.new(str(transaction).encode('utf-8'))
        return verifier.verify(h, binascii.unhexlify(signature))

    def submit_transaction(self, sender_address, sender_private_key, recipient_address, value):
        """
        Add a transaction to transactions array if the signature verified
        """
        transaction = OrderedDict({
            'sender_address': sender_address,
            'recipient_address': recipient_address,
            'value': value
        })

        # If it's a mining reward, skip the signature process
        if sender_address == MINING_SENDER:
            self.transactions.append(transaction)
            return len(self.chain) + 1

        # Manages transactions from wallet to another wallet
        else:
            transaction_signature = self.sign_transaction(
                sender_private_key=sender_private_key,
                transaction=transaction
            )
            transaction_verification = self.verify_transaction_signature(
                sender_address=sender_address,
                signature=transaction_signature,
                transaction=transaction
            )

            if transaction_verification:
                self.transactions.append(transaction)
                return len(self.chain) + 1
            else:
                return False

    def get_balance(self, address):
        """
        Calculate the balance of a wallet by iterating over the blockchain.
        """
        balance = 0.0

        # Iterate through all blocks in the chain
        for block in self.chain:
            # Iterate through all transactions in each block
            for transaction in block['transactions']:
                # Check if the wallet is the sender
                if transaction['sender_address'] == address:
                    balance -= transaction['value']

                # Check if the wallet is the recipient
                if transaction['recipient_address'] == address:
                    balance += transaction['value']

        return balance

    def get_available_balance(self, address):
        """
        Calculate the user's available balance, including both confirmed transactions (in blocks)
        and pending transactions (in the transaction pool).
        """
        confirmed_balance = self.get_balance(
            address)  # Balance from mined blocks

        # Now, adjust the balance by considering pending transactions
        pending_debits = 0
        pending_credits = 0

        for transaction in self.transactions:  # Loop through pending transactions
            if transaction['sender_address'] == address:
                # Subtract pending debits
                pending_debits += transaction['value']
            if transaction['recipient_address'] == address:
                pending_credits += transaction['value']  # Add pending credits

        # Available balance is confirmed balance minus pending debits plus pending credits
        available_balance = confirmed_balance - pending_debits + pending_credits
        return available_balance

    def create_block(self, nonce, previous_hash):
        """
        Add a block of transactions to the blockchain
        """
        block = {'block_number': len(self.chain) + 1,
                 'timestamp': time(),
                 'transactions': self.transactions,
                 'nonce': nonce,
                 'previous_hash': previous_hash}

        # Reset the current list of transactions
        self.transactions = []

        self.chain.append(block)
        return block

    def hash(self, block):
        """
        Create a SHA-256 hash of a block
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()

        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self):
        """
        Proof of work algorithm
        """
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)

        nonce = 0
        while self.valid_proof(transactions=self.transactions, last_hash=last_hash, nonce=nonce) is False:
            nonce += 1

        return nonce

    def valid_proof(self, transactions, last_hash, nonce, difficulty=MINING_DIFFICULTY):
        """
        Check if a hash value satisfies the mining conditions. This function is used within the proof_of_work function.
        """
        guess = (str(transactions)+str(last_hash)+str(nonce)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:difficulty] == '0'*difficulty

    def valid_chain(self, chain):
        """
        check if a bockchain is valid
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            # print(last_block)
            # print(block)
            # print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            # Delete the reward transaction
            transactions = block['transactions'][:-1]
            # Need to make sure that the dictionary is ordered. Otherwise we'll get a different hash
            transaction_elements = [
                'sender_address', 'recipient_address', 'value']
            transactions = [OrderedDict(
                (k, transaction[k]) for k in transaction_elements) for transaction in transactions]

            if not self.valid_proof(transactions=transactions, last_hash=block['previous_hash'], nonce=block['nonce']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Resolve conflicts between blockchain's nodes
        by replacing our chain with the longest one in the network.
        """
        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            print('http://' + node + '/chain')
            response = requests.get(
                url='http://' + node + '/chain', timeout=10)

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True

        return False
