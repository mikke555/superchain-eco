import json

from models.network import Network

#######################################################################
#                           Network Config                            #
#######################################################################


ethereum = Network(
    name="ethereum",
    rpc_url="https://rpc.ankr.com/eth",
    explorer="https://etherscan.io",
    eip_1559=True,
    native_token="ETH",
)

optimism = Network(
    name="optimism",
    rpc_url="https://rpc.ankr.com/optimism",
    explorer="https://optimistic.etherscan.io",
    eip_1559=True,
    native_token="ETH",
)


CHAIN_MAPPING = {
    "ethereum": ethereum,
    "optimism": optimism,
}


#######################################################################
#                        SuperChain Contracts                         #
#######################################################################

SAFE_PROXY_FACTORY = "0x4e1DCf7AD4e460CfD30791CCC4F9c8a4f820ec67"
SAFE_L2 = "0x29fcB43b46531BcA003ddC8FCB67FFE91900C762"
SUPERCHAIN_ACCOUNT_SETUP = "0xd2B51c08de198651653523ED14A137Df3aE86Ee0"

# initializer params
SAFE4337_MODULE = "0x75cf11467937ce3F2f357CE24ffc3DBF8fD5c226"
SUPERCHAIN_MODULE = "0x1Ee397850c3CA629d965453B3cF102E9A8806Ded"
SUPERCHAIN_GUARD = "0xaaA5200c5E4C01b3Ea89F175F9cf17438C193abA"

with open("abi/ERC20.json") as f:
    ERC20_ABI = json.load(f)

with open("abi/SafeProxyFactory.json") as f:
    SAFE_PROXY_FACTORY_ABI = json.load(f)

with open("abi/ERC1967Proxy.json") as f:
    SUPERCHAIN_MODULE_ABI = json.load(f)

with open("abi/SuperChainAccountSetup.json") as f:
    SUPERCHAIN_ACCOUNT_SETUP_ABI = json.load(f)

with open("abi/SafeL2.json") as f:
    SAFE_L2_ABI = json.load(f)


#######################################################################
#                         Nouns Contracts                             #
#######################################################################

NOUNS_SEEDER = "0xCC8a0FB5ab3C7132c1b2A0109142Fb112c4Ce515"
NOUNS_DESCRIPTOR_V2 = "0x6229c811D04501523C6058bfAAc29c91bb586268"

with open("abi/NounsSeeder.json") as f:
    NOUNS_SEEDER_ABI = json.load(f)
