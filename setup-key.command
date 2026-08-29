#!/bin/zsh
cd "$(dirname "$0")" || exit 1
python3 skills/yuntu-media-research/scripts/configure_key.py
status=$?
echo
if [ $status -eq 0 ]; then
  echo "配置完成。现在可以运行RedFox采集。"
else
  echo "配置失败，请检查Python是否已安装。"
fi
read "reply?按回车键关闭窗口..."
exit $status
