

### import the libraries
import datetime
import hashlib
import json
from flask import Flask,jsonify,request
import requests
from uuid import uuid4
from urllib.parse import urlparse

## PArt 1- Building the BlockChain

class SupplyChain:
    def __init__(self):
        self.chain=[]
        self.transactions=[]
        self.nodes=set()
        self.create_block(proof=1,previous_hash='0')
        
    def create_block(self,proof,previous_hash):
        block={'index':len(self.chain)+1,
               'timestamp':str(datetime.datetime.now()),
               'proof':proof,
               'previous_hash':previous_hash,
               'transactions':self.transactions
            
            }
        self.transactions=[]
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True 
    
    def add_transaction(self,supplier_no,location_no,dist_no,serial_no,composition,d_category,maf_batch,maf_date):
        self.transactions.append({
            'Supplier ID':supplier_no,
            'Manufacturing location No.':location_no,
            'Distributor No':dist_no,
            'Serial No':serial_no,
            'Chemical Composition' : composition,
            'Drug Category': d_category,
            'Manufacturing Batch':maf_batch,
            'Manufacturing Date':maf_date
            
            })
        previous_block=self.get_previous_block()
        return previous_block['index']+1
    
    def add_node(self,address):
        parsed_url=urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    ### consensus protocol
    
    def replace_chain(self):
        network=self.nodes
        longest_chain=None
        max_length=len(self.chain)
        
        for node in network:
            response=requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
        
            

## Part 2- Mining the BlockChain

app=Flask(__name__)

### creating an address for the node on Port 5000
node_address=str(uuid4()).replace('-','')

### Create The BlockChain
supplychain=SupplyChain()

## Create a web app for the API
### Mining the new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = supplychain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = supplychain.proof_of_work(previous_proof)
    previous_hash = supplychain.hash(previous_block)
    supplychain.add_transaction(supplier_no = 'NA', location_no = 'NA', dist_no='NA', serial_no='NA', composition='NA', d_category ='NA', maf_batch='NA', maf_date='NA')
    block = supplychain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': supplychain.chain,
                'length': len(supplychain.chain)}
    return jsonify(response), 200


# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = supplychain.is_chain_valid(supplychain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200


# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['Supplier ID', 'Manufacturing location No.', 'Distributor No','Serial No','Chemical Composition','Drug Category','Manufacturing Batch','Manufacturing Date']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    index = supplychain.add_transaction(json['Supplier ID'], json['Manufacturing location No.'], json['Distributor No'],json['Serial No'],json['Chemical Composition'],json['Drug Category'], json['Manufacturing Batch'],json['Manufacturing Date'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        supplychain.add_node(node)
    response = {'message': 'All the nodes are now connected. The Blockchain now contains the following nodes:',
                'total_nodes': list(supplychain.nodes)}
    return jsonify(response), 201   

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = supplychain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': supplychain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': supplychain.chain}
    return jsonify(response), 200



# Running the app
app.run(host = '0.0.0.0', port = 1001)
