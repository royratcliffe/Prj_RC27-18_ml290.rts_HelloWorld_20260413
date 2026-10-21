@echo off
set HEXMODX=%1
set INPUT_HEX=%2
set OUTPUT_HEX=%INPUT_HEX:_merge=_merge_out%

REM Run HexmodX process
Call "%HEXMODX%" read -in "%INPUT_HEX%" ^
blkLink -start 0x800C0000 -next 0x80800000 ^
blkLink -start 0x80800000 -next 0x00 ^
writecks -fc set ^
memCopy -from 0x800C0000 -l 0x0073F400 -to 0x800C0000 -o true -fill 0xC3 ^
memCopy -from 0x807FF400 -l 0x00000A20 -to 0x807FF400 -o true -fill 0xC3 ^
memCopy -from 0x80800000 -l 0x00007760 -to 0x80800000 -o true -fill 0xC3 ^
memCopy -from 0x80807760 -l 0x000188A0 -to 0x80807760 -o true -fill 0xC3 ^
memDelete -from 0x08FC0000 -l 0x60000 ^
compfc -fc set ^
comp -addr 0x80800000 -depaddr 0x800C0000 ^
writecks -fc set ^
write -out "%OUTPUT_HEX%" -lyt 0x20

REM Replace original hex with processed hex
copy /Y "%OUTPUT_HEX%" "%INPUT_HEX%" >nul
del "%OUTPUT_HEX%" >nul

exit /B

