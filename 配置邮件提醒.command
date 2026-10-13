#!/bin/zsh
cd "$(dirname "$0")" || exit 1
python3 configure-mail.py
read -r 'reply?按回车关闭窗口…'
