import binascii
import Crypto
from Crypto.PublicKey import RSA
from flask import Blueprint, jsonify, request

from transactions import Transaction


bp = Blueprint('routes', __name__)


@bp.route('/')
def home():
    return jsonify({"message": "Welcome to Flask!"})


wallets = {}


@bp.route('/wallet/new', methods=['GET'])
def new_wallet():
    random_gen = Crypto.Random.new().read
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.publickey()

    public_key_str = binascii.hexlify(
        public_key.exportKey(format='DER')).decode('ascii')
    private_key_str = binascii.hexlify(
        private_key.exportKey(format='DER')).decode('ascii')

    # Save wallet in a dictionary with initial balance of 0
    wallets[public_key_str] = {
        'private_key': private_key_str,
        'balance': 100  # Starting each wallet with a 100
    }

    response = {
        'private_key': private_key_str,
        'public_key': public_key_str
    }

    return jsonify(response), 200


@bp.route('/generate/transaction', methods=['POST'])
def generate_transaction():
    sender_address = request.form['sender_address']
    sender_private_key = request.form['sender_private_key']
    recipient_address = request.form['recipient_address']
    value = float(request.form['amount'])

    # Check if sender and recipient exist
    if sender_address not in wallets:
        return jsonify({'error': 'Sender address does not exist.'}), 400

    if recipient_address not in wallets:
        return jsonify({'error': 'Recipient address does not exist.'}), 400

    # Check if sender has enough balance
    if wallets[sender_address]['balance'] < value:
        return jsonify({'error': 'Insufficient balance.'}), 400

    # Create transaction
    transaction = Transaction(
        sender_address, sender_private_key, recipient_address, value)

    # Sign transaction
    response = {
        'transaction': transaction.to_dict(),
        'signature': transaction.sign_transaction()
    }

    # Subtract value from sender and add it to recipient
    wallets[sender_address]['balance'] -= value
    wallets[recipient_address]['balance'] += value

    return jsonify(response), 200
