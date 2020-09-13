from web3 import Web3
import os
import json
from arbHelper import *
import sys

trader = TradingSession("data/credentials.txt", "data/data.json")

if (len(sys.argv) >= 2):
    if (sys.argv[1] == "-update"):
        trader.getPairsFromUniswapV2("UniswapV2")

## Grabbing our generated pairs from Uniswap
with open("data/UniSwapV2Pairs.json", 'r') as file:
    uniPairs = json.load(file)

## Checking some exchange prices
trader.getPriceInfoByPair(uniPairs, list(uniPairs.keys()))
