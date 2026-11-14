#!/bin/sh
# usage: run.sh script.lua prefix first last
cd /d/claude/GAMES/electronic_detective/mame
for i in $(seq $3 $4); do
  ED_SEED=$i ED_OUT=D:/claude/GAMES/electronic_detective/research/data/$2_$i.tsv timeout 600 ./mame.exe elecdet -rompath roms -video none -sound none -nothrottle -skip_gameinfo -autoboot_script ../research/$1 -autoboot_delay 0 >/dev/null 2>&1 &
  if [ $((i % ${PAR:-6})) -eq 0 ]; then wait; fi
done
wait
