# arbitrageTrackerV1

A basic app which uses web3.py and the etherscan.io api to examine the blockchain and find arbitrage opportunities across ERC-20 compliant tokens. User can load in  an arbitrary amount of ERC-20 tokens by specifying them within data.json. 

The app is capable of reading and writing data, and generates and stores a list of trading pairs and their corresponding Uniswap Smart Contract if the -update argument is passed through CLI. This is so that the app doesn't have to look up every Uniswap exchange address at runtime. 

The coolest part about this project is that it actually works, at least for stablecoints: **here's some sample output**:

```
Trading Pair:    Token 1 liquidity:           Token 2 liquidity:    Uniswap2 Price:                        Kyberswap Min. Price:
---------------  ---------------------------  --------------------  -------------------------------------  ----------------------------
DAI/USDT         1554006.946 DAI              1575859.933 USDT      0.986DAI/USDT                          0.983DAI/USDT
DAI/LINK         82.712 DAI                   1027.409 LINK         0.081DAI/LINK                          0.081DAI/LINK
DAI/USDC         1437613.782 DAI              1461538.788 USDC      0.984DAI/USDC                          0.983DAI/USDC
DAI/WETH         26745560.671 DAI             75080.218 WETH        356.226DAI/WETH                        345.454DAI/WETH
DAI/sUSD         67.280 DAI                   66.735 sUSD           1.008DAI/sUSD                          1.001DAI/sUSD
USDT/LINK        442813253798507.500 USDT     0.000 LINK            82573202816319507922944.000USDT/LINK   79898721125.494USDT/LINK
USDT/USDC        7200650.193 USDT             7196308.107 USDC      1.001USDT/USDC                         964716419700.000USDT/USDC
USDT/WETH        203222085572909920.000 USDT  0.000 WETH            2761399419255379722240.000USDT/WETH    350215636560000.000USDT/WETH
USDT/sUSD        30519.417 USDT               0.000 sUSD            30519417078999995645952.000USDT/sUSD   982484947415.431USDT/sUSD
USDC/LINK        11.846 LINK                  153.111 USDC          0.077USDC/LINK                         0.000USDC/LINK
LINK/WETH        821962.350 LINK              27427.984 WETH        29.968LINK/WETH                        28.981LINK/WETH
USDC/WETH        50983564.174 USDC            141229.297 WETH       360.998USDC/WETH                       349929386650000.000USDC/WETH
USDC/sUSD        641424.817 USDC              0.000 sUSD            641424817384999899627520.000USDC/sUSD  984224665654.783USDC/sUSD
sUSD/WETH        11490964.383 WETH            31650.355 sUSD        363.060sUSD/WETH                       354.774sUSD/WETH
```

**Takeaways for V2**

V1 surprised me as it tracks stablecoins really well - this is because they have the same amount of decimals (in general). You can actually run this script and go and confirm prices on UniswapV2 and KyberSwap, which is really cool (though the Uniswap prices are consistently off by a few decimals - I suspect that this is because they're using time-adjusted average pricing and I'm taking a point price, but that's just a hunch.

Uniswap also has a weird ordering conventions, which means that sometimes the Kyberswap lookup can get messed up, especially if the tokens have different decimals. This shows in the above as pools which supposedly have 0 liquidity - this isn't true, they're just using the wrong decimal count.

I suspect that this is because my implementation of currency pairs is pretty lacking and not formal enough - in V2, I'm actually going to implement pairs as a key underlying data structure, and hope that I can implement some more flexibility vis a vis Kyber/UniswapV2 that way. I also want to implement Sushiswap support, and focus on client-side performance - that means as few server calls as possible. I know I can implement exchange lookup algorithmically for UniswapV2 (and probably Sushiswap, it being a fork and all)

I should also add a column for arbitrage opportunity in percent!
