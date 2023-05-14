# rec-radio
よくある、ラジオ番組の録音用のpythonスクリプト

## 仕様
### NHKラジオの録音用
```
usage: rec_nhk.py [-h] [--timing [{previous,following,present}]] [-c] channel duration [outputdir] [Prefix name]

Recording NHK radio.

positional arguments:
  channel               Channel Name
  duration              Duration(minutes)
  outputdir             Output path default:'.'
  Prefix name           Prefix name for output file.

optional arguments:
  -h, --help            show this help message and exit
  --timing [{previous,following,present}]
  -c, --cleanup         Cleanup(remove) output file which recording is not completed.
```
### radiko用
```
usage: rec_radiko.py [-h] [-c] channel duration [outputdir] [Prefix name]

Recording Radiko.

positional arguments:
  channel        Channel Name
  duration       Duration(minutes)
  outputdir      Output path default:'.'
  Prefix name    Prefix name for output file.

optional arguments:
  -h, --help     show this help message and exit
  -c, --cleanup  Cleanup(remove) output file which recording is not completed.
```

### radikoの番組表検索
```
usage: find_radiko.py [-h] -k KEYWORD [-a AREA_ID]

find keyword in Radiko program.

optional arguments:
  -h, --help            show this help message and exit
  -k KEYWORD, --keyword KEYWORD
                        keyword to be finded in Radiko program.
  -a AREA_ID, --area_id AREA_ID
                        area_id in Radiko program(API). ex) 'JP13' is for tokyo/japan
```

### タイムフリー録音
```
usage: tfrec_radiko.py [-h] -s STATION -ft FROMTIME -to TOTIME [-c] [outputdir] [Prefix-name]

Recording time-free-Radiko.

positional arguments:
  outputdir             Output path default:'.'
  Prefix-name           Prefix name for output file.

optional arguments:
  -h, --help            show this help message and exit
  -s STATION, --station STATION
                        Recording station.
  -ft FROMTIME, --fromtime FROMTIME
                        from time
  -to TOTIME, --totime TOTIME
                        to time
  -c, --cleanup         Cleanup(remove) output file which recording is not completed.
  ```
