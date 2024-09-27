# ChainAlchemy 
[![License: Unlicense](https://img.shields.io/badge/license-Unlicense-blue.svg?logo=unlicense)](https://unlicense.org/)
[![codecov](https://codecov.io/gh/hamdi3/ChainAlchemy/branch/main/graph/badge.svg)](https://codecov.io/gh/hamdi3/ChainAlchemy/branch/main)
[![Build Status](https://github.com/hamdi3/ChainAlchemy/actions/workflows/pr_tests.yml/badge.svg)](https://github.com/hamdi3/ChainAlchemy/actions/workflows/pr_tests.yml)
![Python Version](https://img.shields.io/badge/python-3.12-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0.3-red.svg?logo=flask)
![Docker](https://img.shields.io/badge/docker-085E8A.svg?logo=docker&logoColor=white)
[![Swagger](https://img.shields.io/badge/Swagger-API-green?logo=swagger)](http://localhost:5000/swagger/)

ChainAlchemy is a blockchain application that provides a comprehensive system for creating and managing wallets, processing transactions, mining blocks, and achieving consensus between nodes. It offers a RESTful API built with Flask to facilitate interaction with the blockchain.

## Table of Contents

- [Features](#Features)
- [Installation](#Installation)
- [Docker Support](#Docker-Support)
- [Usage](#Usage)
- [API Endpoints](#API-Endpoints)
  - [Wallet Management](#Wallet-Management)
  - [Transactions](#Transactions)
  - [Blockchain Operations](#Blockchain-Operations)
  - [Node Management](#Node-Management)
- [Testing](#Testing)
- [License](#License)

---

## Features

- Wallet creation with private and public key generation
- Transaction submission and validation
- Mining new blocks with proof of work
- Node registration and consensus mechanisms
- Full blockchain retrieval and validation

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/hamdi3/ChainAlchemy.git
cd ChainAlchemy
```

### Install Dependencies
You can install the necessary dependencies using `pip`:
```bash
pip install -r requirements.txt
```

## Docker-Support

ChainAlchemy supports running the application via Docker for easy deployment and management. Follow the steps below to build and run the Docker container.

### Step 1: Build the Docker Image

First, ensure that Docker is installed on your machine. Then, navigate to the project directory and run the following command to build the Docker image:

```bash
docker build -t chainalchemy:latest .
```

### Step 2: Run the Docker Container
Once the image is built, you can run the application in a container using the following command:
```bash
docker run -d -p 5000:5000 --name chainalchemy_container chainalchemy:latest
```
- The `-d `flag runs the container in detached mode (in the background).
- The `-p 5000:5000` option maps port 5000 on your host machine to port 5000 inside the container.
- `--name chainalchemy_container` assigns a name to the running container.

### Step 3: Access the Application
Once the container is running, you can access the ChainAlchemy API at:
```bash
localhost:5000
```

### Step 4: Stopping the Container
To stop the running container, use the following command:
```bash
docker stop chainalchemy_container
```

### Step 5: Removing the Container
To remove the container after stopping it, use the following command:
```bash
docker rm chainalchemy_container
```

## Usage

### Running the Application
Once everything is set up, you can run the Flask application:
```bash
python src/main.py
```
The API will now be available on `http://localhost:5000`.

### Swagger UI
To explore the API documentation interactively, visit the Swagger UI on `http://localhost:5000/swagger/`

## API-Endpoints

### Wallet-Management

#### Create a New Wallet
POST /wallet/new
Generates a new wallet with a public/private key pair.

**Response:**
- `200 OK`: Wallet created successfully with public and private keys.

### Transactions

#### Submit a New Transaction
POST /transactions/new
Submit a transaction from one wallet to another.

**Required fields:**
- `sender_address`: Sender's public address
- `sender_private_key`: Sender's private key
- `recipient_address`: Recipient's public address
- `amount`: Transaction amount

**Response:**
- `201 Created`: Transaction will be added to the blockchain.
- `400 Bad Request`: Missing required fields or insufficient balance.
- `406 Not Acceptable`: Invalid transaction.

#### Get All Pending Transactions
GET /transactions/get
Retrieve a list of all transactions in the current pending pool.

**Response:**
- `200 OK`: Returns a list of pending transactions.

### Blockchain-Operations

#### Get the Full Blockchain
GET /chain
Retrieve the entire blockchain.

**Response:**
- `200 OK`: Returns the blockchain and its length.

#### Mine a New Block
POST /mine
Mine a new block and reward the miner.

**Required fields:**
- `miner_address`: The public address of the miner to receive rewards.

**Response:**
- `200 OK`: Block mined and added to the chain.
- `400 Bad Request`: Missing required fields.

### Node-Management

#### Register a New Node
POST /nodes/register
Register a new node for consensus.

**Required fields:**
- `nodes`: A non-empty list of node URLs.

**Response:**
- `201 Created`: Nodes successfully registered.
- `400 Bad Request`: Invalid or missing node list.

#### Get All Registered Nodes
GET /nodes/get
Retrieve a list of all nodes in the network.

**Response:**
- `200 OK`: Returns a list of nodes.

#### Resolve Node Conflicts (Consensus)
GET /nodes/resolve
Reach consensus across the nodes, resolving conflicts.

**Response:**
- `200 OK`: Returns the authoritative chain or indicates that the chain was replaced.

## Testing
You can run the unit tests & generate coverage reports for this project using `pytest`:
```bash
pytest --cov-report term --cov-report xml:tests/coverage.xml --cov=src/
```

## License

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this software dedicate any and all copyright interest in the software to the public domain. We make this dedication for the benefit of the public at large and to the detriment of our heirs and successors. We intend this dedication to be an overt act of relinquishment in perpetuity of all present and future rights to this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT, OR OTHERWISE, ARISING FROM, OUT OF, OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>

