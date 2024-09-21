import binascii
import Crypto
from Crypto.PublicKey import RSA
from flask import Blueprint, jsonify, request

from transactions import Transaction


bp = Blueprint('routes', __name__)


@bp.route('/')
def home():
    return jsonify({"message": "Welcome to Flask!"})


@bp.route('/wallet/new', methods=['GET'])
def new_wallet():
    random_gen = Crypto.Random.new().read
    private_key = RSA.generate(1024, random_gen)
    public_key = private_key.publickey()
    response = {
        'private_key': binascii.hexlify(private_key.exportKey(format='DER')).decode('ascii'),
        'public_key': binascii.hexlify(public_key.exportKey(format='DER')).decode('ascii')
    }

    return jsonify(response), 200


@bp.route('/generate/transaction', methods=['POST'])
def generate_transaction():

    sender_address = request.form['sender_address']
    sender_private_key = request.form['sender_private_key']
    recipient_address = request.form['recipient_address']
    value = request.form['amount']

    transaction = Transaction(
        sender_address, sender_private_key, recipient_address, value)

    response = {'transaction': transaction.to_dict(
    ), 'signature': transaction.sign_transaction()}

    return jsonify(response), 200
