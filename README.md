# yolokey-server
Automatic deployment of fastd public keys. Accept everyone's keys!

## Set up
    sudo apt-get install python3-pip python3-virtualenv python3-dev
    git clone https://github.com/hackspace-marburg/yolokey-server.git
    cd yolokey-server/
    ./bootstrap.sh

## Environment variables
* `FASTD_SITE`: fastd site / interface (`systemctl reload fastd@….service`)
* `FASTD_PEERS_DIR`: fastd peer directory (`include peers from "…";`)
