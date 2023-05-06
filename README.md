# rec-radio
よくある、ラジオ番組の録音用のpythonスクリプト

# 仕様
NHKラジオの録音用
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
radiko用
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

## メモ
radikoの番組表xlmの取得APIのメモ（https://ststarfield.blog.fc2.com/blog-entry-150.html）

【ステーションリスト】

http://radiko.jp/v3/station/list/JP13.xml

->　東京の場合 JP13
->　JP+都道府県コード　　ex) 北海道 => JP1　　沖縄=> JP47

＜参考＞　http://nlftp.mlit.go.jp/ksj/gml/codelist/PrefCd.html　国土交通省

＜全放送局取得＞
http://radiko.jp/v3/station/region/full.xml

【番組表（エリア別）】

＜今現在＞
http://radiko.jp/v3/program/now/JP13.xml

＜本日＞
http://radiko.jp/v3/program/today/JP13.xml

＜日付指定＞
http://radiko.jp/v3/program/date/20171019/JP13.xml
->　yyyy年mm月dd日　yyyymmdd　　ex)2017年4月1日 => 20170401

【番組表（放送局別）】

＜週間番組表（前後１週間）＞
http://radiko.jp/v3/program/station/weekly/FMT.xml
-> station_id + .xml ex) TOKYO FM => FMT　　TBSラジオ => TBS
（station_id　は　ステーションリストから取得可能）

＜今日＞
http://radiko.jp/v3/program/station/today/FMT.xml

＜日付指定＞
http://radiko.jp/v3/program/station/date/20171019/FMT.xml
