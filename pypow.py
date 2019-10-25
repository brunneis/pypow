#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import randint
import hashlib
import time
from catenae import Link, Electron, rpc, should_stop
from threading import Lock
from os import environ
import time

from urllib import request


def get_current_iss_location():
    url = 'http://api.open-notify.org/iss-now'
    return request.urlopen(url).read().decode('utf-8')


class BlockchainUtils:
    @staticmethod
    def sha3_256(text: str):
        return hashlib.sha3_256(text.encode('utf-8')).hexdigest()

    @staticmethod
    def get_timestamp():
        return int(round(time.time()))

    @staticmethod
    def get_rate(number: int, start_timestamp: int):
        elapsed_seconds = BlockchainUtils.get_timestamp() - start_timestamp
        if elapsed_seconds == 0:
            return number
        return number / elapsed_seconds


class Block:
    def __init__(self, timestamp: int, author: str, prev_hash: str, data: str):
        self.timestamp = timestamp
        self.author = author
        self.prev_hash = prev_hash
        self.data = data
        self.set_nonce()
        self.height = None

    def set_nonce(self):
        self.nonce = randint(0, 0x7FFFFFFF)
        self.hash = Block.get_hash(self)

    @staticmethod
    def get_hash(block: Block):
        data_hash = BlockchainUtils.sha3_256(block.data)
        block_hash = BlockchainUtils.sha3_256(
            f'{block.timestamp}{block.author}{block.prev_hash}{data_hash}{block.nonce}')
        return block_hash


class Blockchain(Link):

    ZEROS_HASH = 64 * '0'  # 0x0000000000000000000000000000000000000000000000000000000000000000
    target = 6 * '0' + 58 * 'f'  # 0x000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffff

    def setup(self):
        self.known_blocks = dict()
        self.unprocessed_blocks = list()
        self.winning_block = None
        self.winning_height = -1

        self.process_blocks()

        self.launch_thread(self.mine, safe_stop=True)
        self.loop(self.write_output, interval=3)

    def find_block(self, prev_hash: str, data: str, mining_preview: bool = True):
        block = Block(BlockchainUtils.get_timestamp(), environ['MINER_NAME'], prev_hash, data)
        start_timestamp = BlockchainUtils.get_timestamp()
        hashrate = 0
        hashes_no = 0
        while block.hash > Blockchain.target:
            if should_stop():
                return
            prev_hash = self.get_prev_hash()
            block.set_nonce()
            hashes_no += 1
            hashrate = BlockchainUtils.get_rate(hashes_no, start_timestamp)
            if mining_preview and hashes_no % 5000 == 0:
                self.logger.log(f'{int(hashrate / 1000)} Kilohashes / second')
        return block

    def process_blocks(self):
        loops = 0
        processed_block_indexes = list()
        for index, block in enumerate(self.unprocessed_blocks):
            if block.prev_hash in self.known_blocks:
                block.height = self.known_blocks[block.prev_hash].height + 1
                processed_block_indexes.append(index)
            elif block.prev_hash == Blockchain.ZEROS_HASH:
                block.height = 0
                processed_block_indexes.append(index)
            else:
                continue

        processed_block_indexes = reversed(sorted(processed_block_indexes))
        for index in processed_block_indexes:
            block = self.unprocessed_blocks.pop(index)
            self.update_winning_block(block)
            self.known_blocks[block.hash] = block

    def update_winning_block(self, block):
        if block.height > self.winning_height:
            self.winning_height = block.height
            self.winning_block = block

    @rpc
    def send_block(self, block: Block, context=None):
        block.hash = Block.get_hash(block)
        if block.hash > Blockchain.target:
            self.logger.log(f'❌ Rejected block {block.hash} from {block.author}', level='warn')
        elif block.hash not in self.known_blocks:
            self.logger.log(f'📥 Storing block {block.hash} from {block.author}')
            self.unprocessed_blocks.append(block)
            self.process_blocks()

    def write_output(self):
        if self.winning_block is None:
            return
        block = self.winning_block

        with open('winning_chain.txt', 'w') as output_file:
            while block.prev_hash != Blockchain.ZEROS_HASH or block.prev_hash == Blockchain.ZEROS_HASH:
                output_file.write(83 * '-' + '\n')
                output_file.write(f'| hash:       | {block.hash}\n')
                output_file.write(f'| height:     | {block.height}\n')
                output_file.write(f'| timestamp:  | {block.timestamp} ({time.ctime(block.timestamp)})\n')
                output_file.write(f'| author:     | {block.author}\n')
                output_file.write(f'| prev_hash:  | {block.prev_hash}\n')
                output_file.write(f'| data:       | {block.data}\n')
                output_file.write(83 * '-' + '\n')

                if block.prev_hash != Blockchain.ZEROS_HASH:
                    block = self.known_blocks[block.prev_hash]
                else:
                    break

    def mine(self):
        blocks_no = 0
        start_timestamp = BlockchainUtils.get_timestamp()

        while not should_stop():
            prev_hash = self.get_prev_hash()

            block = self.find_block(prev_hash, '')
            if not block:
                return

            blocks_no += 1
            blockrate = BlockchainUtils.get_rate(blocks_no, start_timestamp)
            self.logger.log(f'Valid block {block.hash} found! {int(blockrate * 3600)} blocks / hour\n')

            self.send_block(block)
            self.rpc_notify('send_block', block)

    def get_prev_hash(self):
        if self.winning_block:
            prev_hash = self.winning_block.hash
        else:
            prev_hash = Blockchain.ZEROS_HASH
        return prev_hash


Blockchain(uid_consumer_group=True).start()