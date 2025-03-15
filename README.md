# BOSS-PIC-Simulator

## 概要
本リポジトリには2つの開発支援ソフトが含まれる。
両ソフトの目的はMCUの開発環境支援である。

#### BOSS PIC Simulator
BOSS-PIC-Simulatorは、MOMIJIにおけるBOSS PICの動作を再現したものである。
本ソフトからは実際に衛星環境で想定するコマンドが送信される。それに対し適切な返信をすることで状況に合わせた通信が続く。
#### CMD Transimtter
CMD Transmitterは、BOSS-PIC-Simulatorより柔軟なコマンド、タイミングで送信できるものである。
SFDチェック、CRCチェックはされるが、特に入力に対して何かしらの動作を取ることはない。


## 環境
#### 言語
Python
#### 使用ライブラリ
```
pyserial==3.5
pywin32==308
wcwidth==0.2.13
```
これ以外のバージョンでも十分に動作すると思われるが検証はしていない


## 使用方法
### 基本操作
1. ソフトの実行機器とMIS MCUをUARTで接続する。
2. ソフトを実行する。
3. 使用するCOMポートを入力する
4. その後ソフト内の指示に従い機器の選択やコマンドの入力を行う。


## 設定
各ソフトのソースコードの上にの各値を操作することでソフトの挙動を変更できる。
- BOSS_PIC_simulator
  - retransmit_time(integer): 再送回数を定義する
  - timeout(floay): 再送までの時間を定義する
  - permission_probability(float 0.0 ~ 1.0): SMF使用要求に対する許可の確率を定義する
  - wait_time: 他の機器との通信時間を定義する
  - debug_mode(bool): 本来UARTでの入力信号によりソフトが動作するが、それをPCからの入力で代替するデバッグモードへ変更する

- CMD_transmitter
  - retransmit_time: 同上
  - timeout: 同上
  - is_add_SFD(bool): 送信コマンドに自動的にSFDを付与するか否か
  - is_add_CRC(bool): 送信コマンドに自動的にCRCを付与するか否か

## トラブルシュート
問題が発生した場合、開発者、管理者に連絡すること。(GARDENs 5号機 OBC武富)
GitHubのIssueなどに報告しても気づかない場合があるので、使用しないこと。
ソフトの異常終了などが発生した場合、コマンドラインのエラーログのテキストをコピー、またはスクリーンショットを取り開発者に送ること。

