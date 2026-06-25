# Slay the Spire 2 AI Stream

Slay the Spire 2 `public-beta`を対象に、強化学習AIの学習状況と観賞用プレイをYouTube/Discordへ流すための実装です。

現時点ではPhase 0/0.5として、実ゲーム接続前に使えるControl UI/API、CLI、Telemetry、mockプロセス管理を実装しています。

## Quick Start

```bash
cp .env.example .env
export PYTHONPATH="$PWD/src"
export CONTROL_AUTH_TOKEN="change-me"
python3 -m sts2_ai_stream.cli serve-control
```

別端末またはブラウザから以下へアクセスします。

```text
http://<ubuntu-server-ip>:8080
```

CLIから操作する場合:

```bash
export PYTHONPATH="$PWD/src"
export CONTROL_AUTH_TOKEN="change-me"
python3 -m sts2_ai_stream.cli status
python3 -m sts2_ai_stream.cli start training
python3 -m sts2_ai_stream.cli logs training
python3 -m sts2_ai_stream.cli reset-model --reason "fresh experiment"
```

`scripts/sts2ctl`も同じCLIを呼び出します。

## 現在できること

- `0.0.0.0:8080`でControl UI/APIを起動
- Bearer tokenまたはログインフォームによる認証
- mock serviceのstart/stop/restart
- service別ログtail
- model namespace reset
- checkpoint alias管理の土台
- JSONL event/audit log出力
- Steam `public-beta` branch/build確認スクリプトの雛形
- Bridge smoke testスクリプトの雛形

## Ubuntuセットアップ

Steam/Slay the Spire 2/STS2MCPの導入は [docs/setup_ubuntu.md](docs/setup_ubuntu.md) を参照してください。

## 注意

Control UIは学習停止やモデルリセットを扱う強い操作画面です。実運用では`CONTROL_AUTH_TOKEN`を必ず変更し、必要に応じてファイアウォールやSSH tunnelで接続元を制限してください。
