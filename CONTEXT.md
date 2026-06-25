# STS2AI Handoff Context

このファイルは、Mac側CodexからUbuntu実機側Codex CLIへ作業を引き継ぐための文脈メモです。

## Project Goal

Slay the Spire 2を強化学習AIが学習していく様子を、YouTube Liveで24時間配信し、節目の結果をDiscordへ通知するシステムを作る。

最初の実装対象は、学習本体よりも運用基盤です。

- Ubuntu CUI環境で動かす。
- SteamCMDでSlay the Spire 2 `public-beta`を入れる。
- STS2MCPをBridgeとして使う。
- Control UI/APIを`0.0.0.0:8080`で立て、ブラウザから起動/停止/ログ/モデルリセットを操作する。
- 学習や配信の本体は後続で差し込む。

## Important Decisions

- Steam beta branch名は`public-beta`。`public_beta`ではない。
- GitHub repositoryは`https://github.com/akkey2017/STS2AI.git`。
- Ubuntu側では、ゲーム本体とAIプロジェクトを分ける。

推奨ディレクトリ:

```text
/srv/sts2/
├── slay_the_spire_2/      # SteamCMDで入れたゲーム本体
└── STS2AI/                # このGit repository
```

- `STS2_GAME_PATH`は`/srv/sts2/slay_the_spire_2`を指す。
- clone先はゲーム本体フォルダの中にしない。
- Bridgeは[Gennadiyev/STS2MCP](https://github.com/Gennadiyev/STS2MCP)を第一候補にする。
- STS2MCPのREST APIは`http://127.0.0.1:15526`想定。
- MCP serverは後で実況/解析/LLM補助に使う。RL学習側はまずREST APIだけを叩く。

## Current Repo State

初回実装済み:

- `PLAN.md`: 全体計画。
- `docs/setup_ubuntu.md`: Ubuntu CUIセットアップ手順。
- `src/sts2_ai_stream/control/`: Control UI/API。
- `src/sts2_ai_stream/cli.py`: `sts2ctl` CLI。
- `src/sts2_ai_stream/telemetry/`: JSONL event/audit log。
- `src/sts2_ai_stream/models/registry.py`: model namespace reset/checkpoint aliasの土台。
- `src/sts2_ai_stream/bridge/client.py`: STS2MCP REST API向けの薄いHTTP client。
- `scripts/check_steam_branch.py`: Steam manifest確認。
- `scripts/smoke_test_bridge.py`: Bridge API疎通確認。
- `scripts/start_broadcast.sh`: FFmpeg/NVENC配信コマンド生成/起動。

確認済み:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m compileall -q src scripts tests
DRY_RUN=1 YOUTUBE_RTMP_URL=rtmp://example.invalid/live2 YOUTUBE_STREAM_KEY=dummy DISPLAY=:100 scripts/start_broadcast.sh
```

Mac側ではControl Serverのローカル起動、token認証、mock service start、model reset、logs/models確認まで済んでいる。

## Ubuntu Setup Status

ユーザーはUbuntu実機にCodex CLIをインストール済み。

Slay the Spire 2について:

- SteamCMDで`app_update 2868840 -beta public-beta validate`を使う。
- `public_beta`では失敗する。

まだ確認が必要:

- Slay the Spire 2本体が`/srv/sts2/slay_the_spire_2`へ入ったか。
- `appmanifest_2868840.acf`がどこにあるか。
- STS2MCPをダウンロードして`mods/`へ配置できるか。
- ゲーム起動後に`http://127.0.0.1:15526`へ接続できるか。

## First Commands On Ubuntu

まだcloneしていない場合:

```bash
mkdir -p /srv/sts2
cd /srv/sts2
git clone https://github.com/akkey2017/STS2AI.git
cd STS2AI
```

`.env`を作る:

```bash
cp .env.example .env
```

最低限、`.env`を以下に合わせる:

```text
STS2_STEAM_APP_ID=2868840
STS2_STEAM_BRANCH=public-beta
STS2_GAME_PATH=/srv/sts2/slay_the_spire_2
STS2_BRIDGE_BASE_URL=http://127.0.0.1:15526
CONTROL_HOST=0.0.0.0
CONTROL_PORT=8080
CONTROL_AUTH_TOKEN=<change-me>
```

テスト:

```bash
export PYTHONPATH="$PWD/src"
python3 -m unittest discover -s tests
```

Control UI起動:

```bash
export PYTHONPATH="$PWD/src"
export CONTROL_AUTH_TOKEN="<change-me>"
scripts/start_control_server.sh
```

別端末から:

```bash
export CONTROL_PUBLIC_BASE_URL=http://127.0.0.1:8080
export CONTROL_AUTH_TOKEN="<change-me>"
scripts/sts2ctl status
scripts/sts2ctl start training
scripts/sts2ctl logs training
scripts/sts2ctl reset-model --reason "ubuntu smoke test"
```

ブラウザから:

```text
http://<ubuntu-server-ip>:8080
```

## Steam / STS2MCP Next Steps

SteamCMD:

```bash
/usr/games/steamcmd
```

SteamCMD内:

```text
force_install_dir /srv/sts2/slay_the_spire_2
login YOUR_STEAM_USERNAME
app_update 2868840 -beta public-beta validate
quit
```

manifest確認:

```bash
find "$HOME" /srv/sts2 -path '*/steamapps/appmanifest_2868840.acf' 2>/dev/null
```

ゲームファイル確認:

```bash
find /srv/sts2/slay_the_spire_2 -maxdepth 4 \( -iname '*Slay*' -o -iname '*.x86_64' \) -type f
```

STS2MCP:

1. https://github.com/Gennadiyev/STS2MCP/releases/latest からrelease assetを取得する。
2. `STS2_MCP.dll`と`STS2_MCP.json`相当のファイルを`/srv/sts2/slay_the_spire_2/mods/`へ置く。
3. ゲームを起動し、SettingsのModsで有効化する。
4. 初回consent dialogを承認する。
5. `curl http://127.0.0.1:15526/`または`scripts/smoke_test_bridge.py`で確認する。

## Suggested First Prompt For Ubuntu Codex

Ubuntu側Codex CLIをこのrepoのrootで起動し、最初にこう依頼するとよい。

```text
CONTEXT.mdとPLAN.mdとdocs/setup_ubuntu.mdを読んで、Ubuntu実機での次の作業を進めてください。
まずは環境確認、Steam/Slay the Spire 2 public-betaのインストール状況確認、Control UIの起動確認、STS2MCP導入準備をお願いします。
分からないことや危険な操作は逐次質問してください。
```

## Open Questions

- Ubuntu実機でのNVIDIA driver / CUDA / NVENC状態。
- XvfbだけでSlay the Spire 2が描画できるか。必要ならXorg dummy、gamescope、weston headlessを検証する。
- STS2MCPの現在releaseが今の`public-beta`に追従しているか。
- STS2MCP REST APIの実レスポンス形状。
- ゲーム多重起動がSteam/ゲーム仕様上どこまで許されるか。
- YouTube stream keyとDiscord webhookの実運用secret管理方法。

