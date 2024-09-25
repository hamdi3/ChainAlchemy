import binascii
import Crypto
from Crypto.PublicKey import RSA
from flask import Blueprint, jsonify, request

from blockchain import Blockchain, MINING_REWARD, MINING_SENDER


bp = Blueprint('routes', __name__)


@bp.route('/')
def home():
    return jsonify({"message": "Welcome to Flask!"})


wallets = {}
blockchain = Blockchain()


@bp.route('/wallet/new', methods=['POST'])
def new_wallet():
    random_gen = Crypto.Random.new().read
    private_key = RSA.generate(3072, random_gen)
    public_key = private_key.publickey()

    public_key_str = binascii.hexlify(
        public_key.exportKey(format='DER')).decode('ascii')
    private_key_str = binascii.hexlify(
        private_key.exportKey(format='DER')).decode('ascii')

    # Save wallet in a dictionary with initial balance of 0
    wallets[public_key_str] = {
        'private_key': private_key_str,
        'balance': 0.0  # Starting each wallet with a 0
    }

    response = {
        'private_key': private_key_str,
        'public_key': public_key_str
    }

    return jsonify(response), 200


@bp.route('/transactions/new', methods=['POST'])
def new_transaction():
    sender_address = request.form['sender_address']
    sender_private_key = request.form['sender_private_key']
    recipient_address = request.form['recipient_address']
    amount = float(request.form['amount'])

    # Dynamically calculate the sender's balance
    sender_balance = blockchain.get_available_balance(address=sender_address)

    # Check if sender and recipient exist (in the current context wallets dictionary)
    if sender_address not in wallets:
        return jsonify({'error': 'Sender address does not exist.'}), 400

    if recipient_address not in wallets:
        return jsonify({'error': 'Recipient address does not exist.'}), 400

    # Check if sender has enough balance dynamically
    if sender_balance < amount:
        return jsonify({'error': 'Insufficient balance.'}), 400

    # Create a new Transaction
    transaction_result = blockchain.submit_transaction(
        sender_address, sender_private_key, recipient_address, amount
    )

    if not transaction_result:
        response = {'message': 'Invalid Transaction!'}
        return jsonify(response), 406
    else:
        response = {
            'message': f'Transaction will be added to Block {str(transaction_result)}'
        }
        return jsonify(response), 201


@bp.route('/transactions/get', methods=['GET'])
def get_transactions():
    # Get pending transactions from transactions pool
    transactions = blockchain.transactions

    response = {'transactions': transactions}
    return jsonify(response), 200


@bp.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


@bp.route('/mine', methods=['POST'])
def mine():
    miner_address = request.form['miner_address']

    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.chain[-1]
    nonce = blockchain.proof_of_work()

    # Submit a reward transaction without a private key (since it's from the system)
    blockchain.submit_transaction(
        sender_address=MINING_SENDER,  # System address for mining rewards
        sender_private_key=None,       # No private key needed for mining rewards
        recipient_address=miner_address,  # Miner receives the reward
        value=MINING_REWARD            # The reward for mining the block
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(nonce, previous_hash)

    response = {
        'message': "New Block Forged",
        'block_number': block['block_number'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash'],
        'miner_balance': blockchain.get_balance(miner_address)
    }
    return jsonify(response), 200


@bp.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.form
    nodes = values.get('nodes').replace(" ", "").split(',')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': [node for node in blockchain.nodes],
    }
    return jsonify(response), 201


@bp.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@bp.route('/nodes/get', methods=['GET'])
def get_nodes():
    nodes = list(blockchain.nodes)
    response = {'nodes': nodes}
    return jsonify(response), 200
