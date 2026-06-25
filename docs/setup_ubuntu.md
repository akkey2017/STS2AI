# Ubuntu CUI Setup

UbuntuのCUI環境で、SteamCMD、Slay the Spire 2 `public-beta`、STS2MCPを入れるための手順です。

## 方針

- CUI運用ではSteam GUIよりSteamCMDを優先する。
- Steam GUIはインストール自体は可能だが、起動にはXorg/Xvfb/VNC/noVNCなどの表示環境が必要になる。
- Slay the Spire 2は有料ゲームなので、SteamCMDはanonymousではなく購入済みSteamアカウントでログインする。
- 初回のMod有効化や同意ダイアログ操作だけ、VNCなどで一度GUI操作が必要になる可能性がある。

## 1. OSパッケージ

```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install -y software-properties-common ca-certificates curl jq unzip git
sudo add-apt-repository -y multiverse
sudo apt update
sudo apt install -y steamcmd xvfb x11-utils libgl1 libegl1 libvulkan1 vulkan-tools
```

`steamcmd`が見つからない場合は、Ubuntuでは`/usr/games/steamcmd`に入っていることがあります。

```bash
which steamcmd || ls -l /usr/games/steamcmd
```

## 2. インストール先

```bash
sudo mkdir -p /srv/sts2/slay_the_spire_2
sudo mkdir -p /srv/sts2/steam-library
sudo chown -R "$USER:$USER" /srv/sts2
```

## 3. Slay the Spire 2 public-betaを入れる

対話式でログインするのが安全です。パスワードをshell historyに残しにくくできます。

```bash
/usr/games/steamcmd
```

SteamCMD内で:

```text
force_install_dir /srv/sts2/slay_the_spire_2
login YOUR_STEAM_USERNAME
app_update 2868840 -beta public-beta validate
quit
```

Steam Guardが有効な場合は、途中でコード入力が求められます。

## 4. インストール結果確認

```bash
find /srv/sts2/slay_the_spire_2 -maxdepth 3 -type f | sort | head -100
find /srv/sts2/slay_the_spire_2 -maxdepth 4 \( -iname '*Slay*' -o -iname '*.x86_64' \) -type f
```

Steam library manifestを使う場合は、`appmanifest_2868840.acf`を探します。

```bash
find "$HOME" /srv/sts2 -path '*/steamapps/appmanifest_2868840.acf' 2>/dev/null
```

見つかったmanifestが例えば`/home/ai/.steam/steam/steamapps/appmanifest_2868840.acf`なら、`STEAM_LIBRARY_PATH`は`/home/ai/.steam/steam`です。

## 5. .env設定

```bash
cp .env.example .env
```

`.env`の最低限:

```text
STS2_STEAM_APP_ID=2868840
STS2_STEAM_BRANCH=public-beta
STEAM_LIBRARY_PATH=/path/to/steam-library-parent
STS2_GAME_PATH=/srv/sts2/slay_the_spire_2
STS2_BRIDGE_BASE_URL=http://127.0.0.1:15526
```

`STEAM_LIBRARY_PATH`がまだ分からない場合も、`STS2_GAME_PATH`が正しければ次の作業は進められます。

## 6. STS2MCP導入

リリース版を使う場合:

1. https://github.com/Gennadiyev/STS2MCP/releases/latest から`STS2_MCP.dll`と`STS2_MCP.json`相当のファイルを取得する。
2. `<game_install>/mods/`にコピーする。
3. ゲームを起動し、SettingsのModsで有効化する。
4. 初回のconsent dialogを承認する。

Linux想定:

```bash
GAME_DIR=/srv/sts2/slay_the_spire_2
MODS_DIR="$GAME_DIR/mods"
mkdir -p "$MODS_DIR"

# ダウンロードしたファイル名に合わせて調整
cp STS2_MCP.dll "$MODS_DIR/"
cp STS2_MCP.json "$MODS_DIR/"
```

有効化後、ゲーム起動中にHTTP APIを確認します。

```bash
curl -s http://127.0.0.1:15526/
scripts/smoke_test_bridge.py
```

## 7. Control UI

```bash
export PYTHONPATH="$PWD/src"
export CONTROL_AUTH_TOKEN="change-me"
scripts/start_control_server.sh
```

ブラウザで:

```text
http://<ubuntu-server-ip>:8080
```

`0.0.0.0`で公開するため、実運用ではファイアウォール、SSH tunnel、または接続元IP制限を併用してください。

