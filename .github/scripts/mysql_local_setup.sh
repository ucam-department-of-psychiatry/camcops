#!/usr/bin/env bash
set -euxo pipefail

sudo systemctl start mysql
mysql -e 'CREATE DATABASE camcops;' -uroot -proot
mysql -e 'CREATE USER `camcops`@`localhost` IDENTIFIED WITH mysql_native_password BY "camcops";' -uroot -proot
mysql -e 'GRANT ALL PRIVILEGES ON `camcops`.* TO `camcops`@`localhost`;' -uroot -proot
