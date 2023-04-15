# rec-radio
よくある、ラジオ番組の録音用のpythonスクリプト

# 仕様
NHKラジオの録音用
```
usage: rec_nhk.py [-h] [--timing [{previous,following,present}]]
                  channel duration [outputdir] [Prefix name]

Recording NHK radio.

positional arguments:
  channel               Channel Name
  duration              Duration(minutes)
  outputdir             Output path default:'.'
  Prefix name           Prefix name for output file.

options:
  -h, --help            show this help message and exit
  --timing [{previous,following,present}]
```
radiko用
```
usage: rec_radiko.py [-h] channel duration [outputdir] [Prefix name]

Recording Radiko.

positional arguments:
  channel      Channel Name
  duration     Duration(minutes)
  outputdir    Output path default:'.'
  Prefix name  Prefix name for output file.

options:
  -h, --help   show this help message and exit
```
