from web3 import Web3
import os
import json
import json
from itertools import combinations
import pdb
import requests
import ast
from tabulate import tabulate

class TradingSession:
    def __init__(self, credentials, database):
        self.credentials = credentials
        self.uni2PairsMap = None

        # Import credentials
        with open(credentials) as file:
            self.provider = file.readline().rstrip('\n')
            self.public = file.readline().rstrip('\n')
            self.private = file.readline().rstrip('\n')
            self.ethscanAPI_Key = file.readline().rstrip('\n')

        # Importing token database, smart contracts
        with open(database) as file:
            self.database = json.load(file)
            self.tokens = self.database["tokens"]
            self.exchanges = self.database["exchanges"]

        # Start web3 instance by connecting to PROVIDER
        self.w3 = Web3(Web3.HTTPProvider(self.provider))

    def getPairsFromUniswapV2(self, exchange):

        factory = self.w3.eth.contract(address = self.exchanges[exchange]["address"],
        abi = self.exchanges[exchange]["ABI"])

        exchangeMap = {}

        ### Trying out some combinatorics - I might be a little rusty. I'm currently saying
        #that order doesn't matter - is there any difference between a USDC/USDT and
        #USDT/USDC trading pair? Not that I know of - Uniswap is weird though, so I
        #could be wrong

        if (exchange == "UniswapV2"):
            for pair in (list(combinations(self.tokens, 2))):

                #Formatting pair names
                token0 = self.tokens[pair[0]]
                token1 = self.tokens[pair[1]]
                tradingPair = (pair[0] + '/' + pair[1])

                #Grab some temporary checksum addresses
                token0Checksum = self.w3.toChecksumAddress(self.tokens[pair[0]]["address"])
                token1Checksum = self.w3.toChecksumAddress(self.tokens[pair[1]]["address"])

                # Now let's check that an address exists
                exchangeAddress = factory.functions.getPair(token0Checksum, token1Checksum).call()

                if (exchangeAddress == "0x0000000000000000000000000000000000000000"):
                    continue

                # If address doesn't bounce, use the etherscan API to grab the abi spec
                req = requests.get("https://api.etherscan.io/api?module=contract&action=getabi&address="
                + exchangeAddress + "&apikey=" + self.ethscanAPI_Key)

                ## Formatting the return so it will be recognized as an ABI.
                ## There's probably a more pythonic way to do this...
                ## UPDATE: The etherscan API is broken and returns a bunch of nested
                ## escape characters. This took longer than expected, but is working
                ## now I think...

                ABI = str(req.content)
                ABI = ABI.replace('\\\\\"', '"')
                ABI = ABI.replace("'", ' " ')
                ABI = ABI.replace(":", ' : ')
                ABI = ABI.lstrip("\"b\'{\\\"status\\\":\\\"1\\\",\\\"message\\\":\\\"OK\\\",\\\"result\\\":\\\"\" \" ")
                ABI = ABI.rstrip("\"}\\\' \" ")

                if (ABI.find("Contract source code not verified") > -1):
                    print("Contract source code not verified! \n Try https://etherscan.io/address/" + exchangeAddress)
                    testString = ""
                    ABI = "***PLACEHOLDER***"
                else:
                    ABI = json.loads(ABI)

                ## Some formatting of pair order - originally went with internal
                ## UniswapV2 pairs, but that was janky so hardcoding

                stablecoins = ["USDT", "USDC", "DAI", "sUSD" ]

                if(token0["sign"] == "WETH"):
                    tradingPair = self.swapOrder(tradingPair)
                    token0, token1 = token1, token0
                    token0Checksum, token1Checksum = token1Checksum, token0Checksum

                elif( (token1["sign"] in stablecoins) and (token0["sign"] not in stablecoins) ):
                    tradingPair = self.swapOrder(tradingPair)
                    token0, token1 = token1, token0
                    token0Checksum, token1Checksum = token1Checksum, token0Checksum


                # Now let's write all of this to a dictionary...
                exchangeMap[tradingPair] = {
                "token0" : self.tokens[pair[0]],
                "token1" : self.tokens[pair[1]],
                "token0Checksum" : token0Checksum,
                "token1Checksum" : token1Checksum,
                "address" : exchangeAddress,
                "ABI" : ABI
                }

                print("Loaded " + tradingPair)


                # ...and write to JSON! Now I don't have to wait for the list to
                # be read every time - helpful if I want to search for more pairs
                # on UniSwap!

        self.uni2PairsMap = exchangeMap
        with open("data/" + exchange + "Pairs.json", "w") as file:
            json.dump(exchangeMap, file)

    def swapOrder(self, pair):
        ## Function to check token order within Uniswap - they're technically interchangeable
        ## but I don't trust their use of the word.
        # def checkPairOrder:

        ## Quick function to swap currency pair strings - I get the sense I'll be
        ## using this a lot
        old_order = pair.split('/')
        return str(old_order[1] + "/" + old_order[0])

    def getPriceInfoByPair(self, pairsMap, pairs):

        formattedOut = []
        kyberAddress = self.w3.toChecksumAddress(self.database["exchanges"]["KyberSwap"]["address"])
        kyberABI = self.database["exchanges"]["KyberSwap"]["ABI"]

        kyberSwap = self.w3.eth.contract(address = kyberAddress, abi = kyberABI)

        for pair in pairs:
            token0 = pairsMap[pair]["token0"]
            token0Checksum = pairsMap[pair]["token0Checksum"]

            token1 = pairsMap[pair]["token1"]
            token1Checksum = pairsMap[pair]["token1Checksum"]



            ## Gathering info from Uniswap V2 and formatting
            uniswapV2 = self.w3.eth.contract(address = pairsMap[pair]["address"],
                                                            abi = pairsMap[pair]["ABI"])

            pool_info = uniswapV2.functions.getReserves().call()
            pool_0 = pool_info[0] / (1 * 10**token0["decimals"])
            pool0string = (format(pool_0, ".3f") + " " + token0["sign"])

            pool_1 = pool_info[1] / (1 * 10**token1["decimals"])
            pool1string = (format(pool_1, ".3f") + " " +token1["sign"])

            price0in1 = (pool_0 / pool_1)
            pricestring0in1 = ((format(price0in1, ".3f")) + pair)

            ## Gathering info from kyberswap and formatting
            ## I'm guessing I need some more logic around this - my pairs are
            ## getting fucked up by Kyber. I'll probably have to dig into
            ## the docs... I hope I don't have to write too much if/else...

            if ((token0["sign"] == "WETH") or (token1["sign"] == "WETH")):
                price = kyberSwap.functions.getExpectedRate(token1Checksum, token0Checksum, (1*10**token1["decimals"])).call()
                # pdb.set_trace()
            else:
                price = kyberSwap.functions.getExpectedRate(token0Checksum, token1Checksum, (100*10**token0["decimals"])).call()

            # Assuming slippage, using minimum return to be safe
            price = price[1]/(1*10**token0["decimals"])

            kyberPriceString = (format(price, ".3f") + pair)


            table = [pair, pool0string, pool1string, pricestring0in1, kyberPriceString]

            formattedOut.append(table)

        headers = ["Trading Pair:", "Token 1 liquidity:", "Token 2 liquidity:", "Uniswap2 Price: ", "Kyberswap Min. Price:"  ]

        print(tabulate(formattedOut, headers = headers, floatfmt=".3f"))







        # For each pair, print a python table containing their name, sign, trade
        # price on exchanges, and arbitrage rate if applicable
        # Start with UniSwapV2 and KyberSwap
