##  🚀 Installation
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## ⚙️ Settings

```env
########################################################################
#                           General Settings                           #
########################################################################

USE_PROXY = True
SHUFFLE_WALLETS = False

SLEEP_BETWEEN_WALLETS = [10, 20]
SLEEP_BETWEEN_ACTIONS = [10, 20]

########################################################################
#                           Action Settings                            #
########################################################################

FUND_VALUE = [0.00003, 0.00006]  # $0.10 - $0.20
DISPERSE_VALUE = [0.000003, 0.00001]  # $0.01 - $0.03
DISPERSE_RECIPIENTS = [1, 3]
```
