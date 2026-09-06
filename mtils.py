import os
import sys

                                                               
                                                      
                                                               
os.environ["QT_LOGGING_RULES"] = "*=false;qt.multimedia*=false;qt.multimedia.ffmpeg*=false"
os.environ["AV_LOG_FORCE_NOCOLOR"] = "1"
os.environ["AV_LOG_LEVEL"] = "quiet"

import json
import time
import subprocess
import shutil
import zipfile
import traceback
import re
import math
import random
import threading
import urllib.request
import urllib.parse
import urllib.error

                                                               
                          
                                                               
def crash_handler(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    print("\n" + "=" * 60)
    print("❌ CRITICAL MTILS FAILURE / CRASH DETECTED")
    print("=" * 60)
    traceback.print_exception(exc_type, exc_value, exc_tb)
    print("=" * 60)
    print("💡 The window is locked from closing. Copy the error above.")
    print("=" * 60)
    try:
        input("\nPress Enter to close the process...")
    except Exception:
        pass

sys.excepthook = crash_handler

                                                               
                                       
                                                               
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
THEMES_DIR = os.path.join(BASE_DIR, "themes")
CREATED_DIR = os.path.join(BASE_DIR, "created")

CF_API_KEY = "you dont need it"

MC_VERSIONS_ORDERED = [
    "1.16.5", "1.17.1", "1.18.2", "1.19.2", "1.19.4",
    "1.20.1", "1.20.2", "1.20.4", "1.20.6", "1.21", "1.21.1"
]

                                                      
REMOTE_THEMES_CACHE = []

def resolve_path(target_path):
    if not target_path:
        return BASE_DIR
    if os.path.isabs(target_path):
        return target_path
    return os.path.abspath(os.path.join(BASE_DIR, target_path))

DEFAULT_CONFIG = {
    "version": "1.0.0",
    "active_theme": "default",
    "theme_settings": {
        "animated_bg": True,
        "block_anim": True,
        "texteffect": True
    },
    "aliases": {
        "m": "mod",
        "s": "server",
        "p": "plugin",
        "dp": "datapack",
        "rp": "respack",
        "cls": "clear",
        "h": "help"
    }
}

state = {
    "bound_server": None,
    "bound_mod": None
}

GUI_WINDOW = None
ANSI_REGEX = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except Exception:
            pass
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CONFIG

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
    except Exception as e:
        print(f" [!] Failed to save config: {e}")

def init_environment():
    for directory in [THEMES_DIR, CREATED_DIR]:
        if os.path.exists(directory) and not os.path.isdir(directory):
            try:
                os.remove(directory)
            except Exception:
                pass
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception:
            pass

    for sub in ["mods", "servers", "plugins", "repacks", "datapacks"]:
        sub_path = os.path.join(CREATED_DIR, sub)
        os.makedirs(sub_path, exist_ok=True)

                                                               
                                                 
                                                               
def fetch_remote_themes_worker():
    global REMOTE_THEMES_CACHE
    discovered = []
    headers = {"User-Agent": "mtils-cli/1.0"}

                                          
    try:
        search_url = "https://api.github.com/search/repositories?q=topic:mtilstheme&sort=updated"
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8-sig"))
            for item in data.get("items", []):
                full_name = item.get("full_name")
                if full_name and full_name not in discovered:
                    discovered.append(full_name)
    except Exception:
        pass

                                                           
    try:
        user_url = "https://api.github.com/users/devoirinyou-ai/repos?per_page=100"
        req = urllib.request.Request(user_url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            repos = json.loads(resp.read().decode("utf-8-sig"))
            if isinstance(repos, list):
                for r in repos:
                    name = r.get("name", "").lower()
                    topics = r.get("topics", [])
                    if "theme" in name or "mtilstheme" in topics or name.startswith("mtils-"):
                        fn = r.get("full_name")
                        if fn and fn not in discovered and name != "mtils":
                            discovered.append(fn)
    except Exception:
        pass

    if discovered:
        REMOTE_THEMES_CACHE = discovered

def start_theme_scanner_thread():
    t = threading.Thread(target=fetch_remote_themes_worker, daemon=True)
    t.start()

def get_pack_format(mc_version):
    table = {
        "1.16.5": 6, "1.17.1": 7, "1.18.2": 8, "1.19.2": 9,
        "1.19.4": 13, "1.20.1": 15, "1.20.2": 18, "1.20.4": 26,
        "1.20.6": 41, "1.21": 48, "1.21.1": 48
    }
    if mc_version.isdigit():
        return int(mc_version)
    return table.get(mc_version.strip(), 15)

def get_forge_version(mc_version):
    table = {
        "1.20.4": "49.0.38", "1.20.2": "48.1.0", "1.20.1": "47.2.0",
        "1.19.4": "45.2.0", "1.19.2": "44.1.0", "1.18.2": "40.2.0",
        "1.16.5": "36.2.39"
    }
    return table.get(mc_version.strip(), "47.2.0")

def get_current_prompt(cfg):
    theme = cfg.get("active_theme", "default")
    prefix = f"mtils [{theme}]"
    if state["bound_server"]:
        prefix += f":srv({os.path.basename(state['bound_server'])})"
    if state["bound_mod"]:
        prefix += f":mod({os.path.basename(state['bound_mod'])})"
    return prefix

def confirm_action(prompt_message):
    global GUI_WINDOW
    if GUI_WINDOW is not None:
        return GUI_WINDOW.ask_confirmation(prompt_message)
    try:
        choice = input(f" [?] {prompt_message} (y/n): ").strip().lower()
        return choice in ["y", "yes"]
    except Exception:
        return False

def show_progress(step, total, action_desc):
    percent = int((step / total) * 100)
    bar_length = 22
    filled = int((step / total) * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    print(f"   [{bar}] {percent:3d}% -> {action_desc}")
    if GUI_WINDOW is not None:
        try:
            from PyQt6.QtWidgets import QApplication
            QApplication.processEvents()
        except Exception:
            pass
    time.sleep(0.04)

def download_file(url, destination, label="Downloading"):
    headers = {"User-Agent": "mtils-minecraft-cli/1.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response, open(destination, "wb") as out_file:
            total_size = int(response.info().get("Content-Length", 0))
            downloaded = 0
            block_size = 65536
            last_percent = -1

            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                downloaded += len(buffer)
                out_file.write(buffer)

                if total_size > 0:
                    percent = int((downloaded / total_size) * 100)
                    if percent != last_percent and percent % 5 == 0:
                        last_percent = percent
                        bar_len = 22
                        filled = int((percent / 100) * bar_len)
                        bar = "█" * filled + "░" * (bar_len - filled)
                        kb_down = downloaded // 1024
                        kb_total = total_size // 1024
                        print(f"   [{bar}] {percent:3d}% ({kb_down}/{kb_total} KB) -> {label}")
                        if GUI_WINDOW is not None:
                            try:
                                from PyQt6.QtWidgets import QApplication
                                QApplication.processEvents()
                            except Exception:
                                pass
        return True
    except Exception as e:
        print(f" [!] Network download failed: {e}")
        return False

def generate_gradle_wrapper(target_dir):
    wrapper_dir = os.path.join(target_dir, "gradle", "wrapper")
    os.makedirs(wrapper_dir, exist_ok=True)
    with open(os.path.join(wrapper_dir, "gradle-wrapper.properties"), "w", encoding="utf-8") as f:
        f.write("""distributionBase=GRADLE_USER_HOME\ndistributionPath=wrapper/dists\ndistributionUrl=https\\://services.gradle.org/distributions/gradle-8.5-bin.zip\nnetworkTimeout=10000\nvalidateDistributionUrl=true\nzipStoreBase=GRADLE_USER_HOME\nzipStorePath=wrapper/dists\n""")
    with open(os.path.join(target_dir, "gradlew.bat"), "w", encoding="utf-8") as f:
        f.write("@rem Gradle startup script for Windows\n@echo off\ngradle %*\n")

def refactor_fabric_template(target_dir, mod_name):
    clean_id = mod_name.lower()
    cap_name = mod_name.capitalize()

    mod_json_path = os.path.join(target_dir, "src", "main", "resources", "fabric.mod.json")
    if os.path.exists(mod_json_path):
        try:
            with open(mod_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["id"] = clean_id
            data["name"] = mod_name
            data["entrypoints"] = {
                "main": [f"com.example.{clean_id}.{cap_name}Mod"]
            }
            data["mixins"] = [f"{clean_id}.mixins.json"]
            with open(mod_json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    res_dir = os.path.join(target_dir, "src", "main", "resources")
    if os.path.exists(res_dir):
        for f in os.listdir(res_dir):
            if f.endswith(".mixins.json"):
                old_mixin = os.path.join(res_dir, f)
                new_mixin = os.path.join(res_dir, f"{clean_id}.mixins.json")
                try:
                    with open(old_mixin, "r", encoding="utf-8") as mf:
                        mdata = json.load(mf)
                    mdata["package"] = f"com.example.{clean_id}.mixin"
                    with open(old_mixin, "w", encoding="utf-8") as mf:
                        json.dump(mdata, mf, indent=2)
                    if old_mixin != new_mixin:
                        os.rename(old_mixin, new_mixin)
                except Exception:
                    pass
                break

    assets_base = os.path.join(res_dir, "assets")
    if os.path.exists(assets_base):
        for item in os.listdir(assets_base):
            item_path = os.path.join(assets_base, item)
            if os.path.isdir(item_path) and item.lower() != clean_id:
                new_asset_path = os.path.join(assets_base, clean_id)
                if os.path.exists(new_asset_path):
                    shutil.rmtree(new_asset_path)
                os.rename(item_path, new_asset_path)
                break

    java_root = os.path.join(target_dir, "src", "main", "java", "com", "example")
    new_pkg_dir = os.path.join(java_root, clean_id)
    os.makedirs(new_pkg_dir, exist_ok=True)

    main_class_file = os.path.join(new_pkg_dir, f"{cap_name}Mod.java")
    with open(main_class_file, "w", encoding="utf-8") as f:
        f.write(f"""package com.example.{clean_id};

import net.fabricmc.api.ModInitializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class {cap_name}Mod implements ModInitializer {{
    public static final String MOD_ID = "{clean_id}";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    @Override
    public void onInitialize() {{
        LOGGER.info("{mod_name} initialized successfully.");
    }}
}}
""")

    new_mixin_dir = os.path.join(new_pkg_dir, "mixin")
    os.makedirs(new_mixin_dir, exist_ok=True)
    mixin_file = os.path.join(new_mixin_dir, f"{cap_name}Mixin.java")
    with open(mixin_file, "w", encoding="utf-8") as f:
        f.write(f"""package com.example.{clean_id}.mixin;

import net.minecraft.server.MinecraftServer;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(MinecraftServer.class)
public class {cap_name}Mixin {{
    @Inject(at = @At("HEAD"), method = "loadWorld")
    private void init(CallbackInfo info) {{
        // Custom mixin injection for {mod_name}
    }}
}}
""")

    for f in ["ExampleMod.java", "mixin", "examplemod"]:
        p = os.path.join(java_root, f)
        if os.path.exists(p) and p != new_pkg_dir:
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                os.remove(p)

    settings_path = os.path.join(target_dir, "settings.gradle")
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "rootProject.name" in content:
                content = re.sub(r"rootProject\.name\s*=.*", f"rootProject.name = '{clean_id}'", content)
            else:
                content += f"\nrootProject.name = '{clean_id}'\n"
            with open(settings_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

                                                               
                                            
                                                               
def get_existing_dirs(subfolder):
    target = os.path.join(CREATED_DIR, subfolder)
    if not os.path.exists(target):
        return []
    return [d for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))]

def get_contextual_suggestions(current_text):
    text = current_text.strip()
    trailing_space = current_text.endswith(" ")
    tokens = text.split() if text else []
    n = len(tokens)

    root_cmds = ["server", "mod", "plugin", "datapack", "respack", "theme", "texteffect", "alias", "clear", "help", "exit"]
    if n == 0:
        return []
    if n == 1 and not trailing_space:
        prefix = tokens[0].lower()
        return [c for c in root_cmds if c.startswith(prefix)]

    cmd = tokens[0].lower()

                           
    if cmd == "server":
        if (n == 1 and trailing_space) or (n == 2 and not trailing_space):
            p = tokens[1].lower() if n == 2 else ""
            subs = ["set", "launch", "close", "desync", "mod", "plugin", "datapack"]
            return [f"server {s}" for s in subs if s.startswith(p)]

        sub = tokens[1].lower()

        if sub == "set":
            srvs = get_existing_dirs("servers")
            p = tokens[2].lower() if (n == 3 and not trailing_space) else ""
            return [f"server set created/servers/{s}" for s in srvs if s.lower().startswith(p)]

        if sub in ["mod", "plugin", "datapack"]:
            if (n == 2 and trailing_space) or (n == 3 and not trailing_space):
                p = tokens[2].lower() if n == 3 else ""
                return [f"server {sub} {src}" for src in ["modrinth", "curseforge"] if src.startswith(p)]
            return []

        if (n == 2 and trailing_space) or (n == 3 and not trailing_space):
            p = tokens[2].lower() if n == 3 else ""
            loaders = ["fabric", "forge", "paper", "purpur"]
            return [f"server {tokens[1]} {ldr}" for ldr in loaders if ldr.startswith(p)]

        if (n == 3 and trailing_space) or (n == 4 and not trailing_space):
            p = tokens[3].lower() if n == 4 else ""
            return [f"server {tokens[1]} {tokens[2]} {v}" for v in MC_VERSIONS_ORDERED if v.startswith(p)]

                        
    if cmd == "mod":
        if (n == 1 and trailing_space) or (n == 2 and not trailing_space):
            p = tokens[1].lower() if n == 2 else ""
            subs = ["set", "export", "desync"]
            return [f"mod {s}" for s in subs if s.startswith(p)]

        sub = tokens[1].lower()
        if sub == "set":
            mods = get_existing_dirs("mods")
            p = tokens[2].lower() if (n == 3 and not trailing_space) else ""
            return [f"mod set created/mods/{m}" for m in mods if m.lower().startswith(p)]

        if (n == 2 and trailing_space) or (n == 3 and not trailing_space):
            p = tokens[2].lower() if n == 3 else ""
            return [f"mod {tokens[1]} {ldr}" for ldr in ["fabric", "forge"] if ldr.startswith(p)]

        if (n == 3 and trailing_space) or (n == 4 and not trailing_space):
            p = tokens[3].lower() if n == 4 else ""
            return [f"mod {tokens[1]} {tokens[2]} {v}" for v in MC_VERSIONS_ORDERED if v.startswith(p)]

        if (n == 4 and trailing_space) or (n == 5 and not trailing_space):
            p = tokens[4].lower() if n == 5 else ""
            return [f"mod {tokens[1]} {tokens[2]} {tokens[3]} {lng}" for lng in ["java", "kotlin"] if lng.startswith(p)]

                           
    if cmd == "plugin":
        if (n == 2 and trailing_space) or (n == 3 and not trailing_space):
            p = tokens[2].lower() if n == 3 else ""
            return [f"plugin {tokens[1]} {plt}" for plt in ["paper", "spigot"] if plt.startswith(p)]

        if (n == 3 and trailing_space) or (n == 4 and not trailing_space):
            p = tokens[3].lower() if n == 4 else ""
            return [f"plugin {tokens[1]} {tokens[2]} {v}" for v in MC_VERSIONS_ORDERED if v.startswith(p)]

                                       
    if cmd in ["datapack", "respack"]:
        if (n == 2 and trailing_space) or (n == 3 and not trailing_space):
            p = tokens[2].lower() if n == 3 else ""
            return [f"{cmd} {tokens[1]} {v}" for v in MC_VERSIONS_ORDERED if v.startswith(p)]

                          
    if cmd == "theme":
        if (n == 1 and trailing_space) or (n == 2 and not trailing_space):
            p = tokens[1].lower() if n == 2 else ""
            subs = ["list", "set", "install", "bg on", "bg off", "anim on", "anim off"]
            return [f"theme {s}" for s in subs if s.startswith(p)]

        sub = tokens[1].lower()
        if sub == "set":
            themes_found = []
            if os.path.exists(THEMES_DIR):
                for d in os.listdir(THEMES_DIR):
                    clean = d.replace(".zip", "")
                    if clean not in themes_found:
                        themes_found.append(clean)
            p = tokens[2].lower() if (n == 3 and not trailing_space) else ""
            return [f"theme set {t}" for t in themes_found if t.lower().startswith(p)]

        if sub == "install":
            p = tokens[2].lower() if (n == 3 and not trailing_space) else ""
                                                                              
            if REMOTE_THEMES_CACHE:
                return [f"theme install {t}" for t in REMOTE_THEMES_CACHE if t.lower().startswith(p) or p in t.lower()]
            return []

                               
    if cmd == "texteffect":
        p = tokens[1].lower() if (n == 2 and not trailing_space) else ""
        return [f"texteffect {s}" for s in ["on", "off"] if s.startswith(p)]

    return []

                                                               
                                     
                                                               
def fetch_modrinth_download(slug, game_version, loader_type, content_type):
    query_params = {
        "game_versions": json.dumps([game_version])
    }
    if content_type in ["mod", "mods"]:
        query_params["loaders"] = json.dumps([loader_type])
    elif content_type in ["plugin", "plugins"]:
        query_params["loaders"] = json.dumps(["paper", "spigot", "bukkit", "purpur"])
    elif content_type in ["datapack", "datapacks"]:
        query_params["loaders"] = json.dumps(["datapack"])

    encoded_query = urllib.parse.urlencode(query_params)
    api_url = f"https://api.modrinth.com/v2/project/{urllib.parse.quote(slug)}/version?{encoded_query}"
    
    req = urllib.request.Request(api_url, headers={"User-Agent": "mtils-minecraft-cli/1.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            versions = json.loads(resp.read().decode())
        
        if not versions:
            fallback_params = {}
            if content_type in ["plugin", "plugins"]:
                fallback_params["loaders"] = json.dumps(["paper", "spigot", "bukkit", "purpur"])
            elif content_type in ["datapack", "datapacks"]:
                fallback_params["game_versions"] = json.dumps([game_version])
            else:
                fallback_params["loaders"] = json.dumps([loader_type])

            fallback_url = f"https://api.modrinth.com/v2/project/{urllib.parse.quote(slug)}/version?{urllib.parse.urlencode(fallback_params)}"
            req_fb = urllib.request.Request(fallback_url, headers={"User-Agent": "mtils-minecraft-cli/1.0"})
            with urllib.request.urlopen(req_fb) as resp_fb:
                versions = json.loads(resp_fb.read().decode())
        
        if not versions:
            return None, None
            
        target_version = versions[0]
        files = target_version.get("files", [])
        if not files:
            return None, None
            
        primary_file = next((f for f in files if f.get("primary")), files[0])
        return primary_file["url"], primary_file["filename"]
    except Exception as e:
        print(f" [!] Modrinth API error: {e}")
        return None, None

def fetch_curseforge_download(slug, game_version, loader_type, content_type):
    search_url = f"https://api.curseforge.com/v1/mods/search?gameId=432&slug={urllib.parse.quote(slug)}"
    headers = {
        "x-api-key": CF_API_KEY,
        "User-Agent": "mtils-minecraft-cli/1.0"
    }
    try:
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
        mods = data.get("data", [])
        if not mods:
            return None, None
        mod_id = mods[0]["id"]
        
        cf_loader_id = 1 if loader_type == "forge" else 4 if loader_type == "fabric" else 6 if loader_type == "neoforge" else None
        
        query_dict = {"gameVersion": game_version}
        if cf_loader_id and content_type in ["mod", "mods"]:
            query_dict["modLoaderType"] = str(cf_loader_id)
            
        files_url = f"https://api.curseforge.com/v1/mods/{mod_id}/files?{urllib.parse.urlencode(query_dict)}"
        req_files = urllib.request.Request(files_url, headers=headers)
        with urllib.request.urlopen(req_files) as resp:
            files_data = json.loads(resp.read().decode())
            
        files_list = files_data.get("data", [])
        
        if not files_list:
            files_url_fallback = f"https://api.curseforge.com/v1/mods/{mod_id}/files?gameVersion={urllib.parse.quote(game_version)}"
            req_fb = urllib.request.Request(files_url_fallback, headers=headers)
            with urllib.request.urlopen(req_fb) as resp_fb:
                fb_data = json.loads(resp_fb.read().decode())
            files_list = fb_data.get("data", [])

        matched_candidates = []
        for candidate in files_list:
            fname = candidate.get("fileName", "").lower()
            gvers = [str(v).lower() for v in candidate.get("gameVersions", [])]

            if content_type in ["mod", "mods"]:
                if loader_type in ["forge", "neoforge"]:
                    if "fabric" in fname or "fabric" in gvers:
                        continue
                elif loader_type == "fabric":
                    if "forge" in fname or "forge" in gvers:
                        continue
            
            matched_candidates.append(candidate)

        if not matched_candidates:
            return None, None
        
        latest = next((f for f in matched_candidates if f.get("releaseType") == 1), matched_candidates[0])
        download_url = latest.get("downloadUrl")
        filename = latest.get("fileName", f"{slug}.jar")
        if not download_url:
            download_url = f"https://edge.forgecdn.net/files/{latest['id'] // 1000}/{latest['id'] % 1000}/{filename}"
        return download_url, filename
    except Exception as e:
        print(f" [!] CurseForge API error: {e}")
        return None, None

def handle_server_install_content(content_type, source, slug):
    if not state["bound_server"] or not os.path.exists(state["bound_server"]):
        print(" [!] No server bound to current session!")
        print("     Bind a server first using: server set created/servers/<name>")
        return

    srv_dir = state["bound_server"]
    source = source.lower()
    content_type = content_type.lower()

    server_version = "1.20.1"
    server_loader = "forge"
    
    meta_path = os.path.join(srv_dir, "mtils_server.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as mf:
                s_meta = json.load(mf)
                server_loader = s_meta.get("loader", server_loader).lower()
                server_version = s_meta.get("version", server_version)
        except Exception:
            pass
    else:
        sp_path = os.path.join(srv_dir, "server.properties")
        if os.path.exists(sp_path):
            with open(sp_path, "r", encoding="utf-8") as f:
                content = f.read()
                m = re.search(r"# mtils (\w+) ([\d\.]+)", content)
                if m:
                    server_loader = m.group(1).lower()
                    server_version = m.group(2)

    if content_type in ["mod", "mods"]:
        dest_folder = os.path.join(srv_dir, "mods")
    elif content_type in ["plugin", "plugins"]:
        dest_folder = os.path.join(srv_dir, "plugins")
    elif content_type in ["datapack", "datapacks"]:
        dest_folder = os.path.join(srv_dir, "world", "datapacks")
    else:
        print(f" [!] Unknown content type '{content_type}'. Use: mod, plugin, datapack")
        return

    os.makedirs(dest_folder, exist_ok=True)
    print(f"\n [*] Querying {source.capitalize()} for '{slug}' (Target: MC {server_version} | Loader: {server_loader.upper()})...")

    if source == "modrinth":
        url, filename = fetch_modrinth_download(slug, server_version, server_loader, content_type)
    elif source in ["curseforge", "curse"]:
        url, filename = fetch_curseforge_download(slug, server_version, server_loader, content_type)
    else:
        print(f" [!] Unknown source '{source}'. Available: modrinth, curseforge")
        return

    if not url:
        print(f" [!] Project '{slug}' not found for MC {server_version} ({server_loader}) on {source.capitalize()}.")
        return

    target_path = os.path.join(dest_folder, filename)
    print(f" [*] Downloading: {filename}")
    success = download_file(url, target_path, f"Installing {content_type}")
    if success:
        print(f" [+] Successfully installed into: {target_path}\n")
    else:
        print(f" [!] Failed to download file from {url}\n")

                                                               
                              
                                                               
def print_help():
    print("""
Available Commands:
  mod <name> <loader> <ver> <lang>        - Setup functional mod project in /created/mods/
  mod set <path>                          - Bind current session to a mod folder
  mod desync                              - Unbind current mod folder
  mod export                              - Build mod and export jar

  server <name> <loader> <ver>            - Setup server (Fabric, Forge, Paper, Purpur) in /created/servers/
  server set <path>                       - Bind current session to a server directory
  server desync                           - Unbind current server directory
  server launch                           - Launch the bound server
  server close                            - Stop the bound server

  server <mod|plugin|datapack> <modrinth|curseforge> <slug>
                                          - Download and install content directly onto bound server

  plugin <name> <loader> <ver>            - Generate Spigot/Paper plugin in /created/plugins/
  respack <name> <ver>                    - Generate resource pack in /created/repacks/
  datapack <name> <ver>                   - Generate datapack in /created/datapacks/

  theme                                   - Show active theme info
  theme list                              - List installed themes (.zip and folders)
  theme set <name>                        - Switch active theme (auto-unpacks .zip)
  theme bg <on/off>                       - Toggle animated background
  theme anim <on/off>                     - Toggle rotating block animation
  theme install <user/repo|keyword>       - Install custom theme directly from GitHub

  texteffect <on/off>                     - Toggle typing glitch effect

  clear                                   - Clear terminal screen
  help                                    - Display this help message
  exit                                    - Terminate mtils session
    """)

def handle_server_command(args, cfg):
    if not args:
        print(" [!] Usage: server <name> <loader> <version>")
        print("     Or:    server <mod|plugin|datapack> <modrinth|curseforge> <slug>")
        print("     Or:    server set <path> | server desync | server launch | server close")
        return

    sub = args[0].lower()

    if sub in ["mod", "plugin", "datapack"] and len(args) >= 3:
        source = args[1]
        slug = args[2]
        handle_server_install_content(sub, source, slug)
        return

    if sub == "set":
        if len(args) < 2:
            print(" [!] Specify path: server set <path>")
            return
        target = resolve_path(args[1])
        if not os.path.exists(target):
            print(f" [!] Path does not exist: {target}")
            return
        state["bound_server"] = target
        print(f" [*] Server directory bound: {target}")
        if GUI_WINDOW is not None:
            GUI_WINDOW.update_prompt_ui()
        return

    if sub == "desync":
        state["bound_server"] = None
        print(" [*] Server directory unbound.")
        if GUI_WINDOW is not None:
            GUI_WINDOW.update_prompt_ui()
        return

    if sub == "launch":
        if not state["bound_server"]:
            print(" [!] No server bound. Use 'server set <path>' first.")
            return
        start_script = "start.bat" if os.name == "nt" else "start.sh"
        full_path = os.path.join(state["bound_server"], start_script)
        if os.path.exists(full_path):
            print(f" [*] Starting server from {full_path}...")
            if os.name == "nt":
                subprocess.Popen(["cmd.exe", "/c", start_script], cwd=state["bound_server"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["bash", start_script], cwd=state["bound_server"])
        else:
            print(f" [!] Launch file '{start_script}' not found in {state['bound_server']}")
        return

    if sub == "close":
        print(" [*] To stop a bound server safely, send 'stop' into its console or press Ctrl+C in its window.")
        return

    name = args[0]
    loader = args[1].lower() if len(args) > 1 else "paper"
    version = args[2] if len(args) > 2 else "1.20.1"
    target_dir = os.path.join(CREATED_DIR, "servers", name)

    if not confirm_action(f"Create server '{name}' ({loader} {version}) in created/servers/?"):
        print(" [-] Operation cancelled by user.")
        return

    print(f"\n [*] Setting up Minecraft Server: {name} [{loader.upper()} {version}]...")

    for folder in ["mods", "config", "world", "plugins"]:
        os.makedirs(os.path.join(target_dir, folder), exist_ok=True)

    meta_path = os.path.join(target_dir, "mtils_server.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"loader": loader, "version": version}, f, indent=4)

                      
    if loader == "fabric":
        print(f" [*] Resolving official Fabric Server launcher for {version} via Fabric Meta API...")
        server_jar_path = os.path.join(target_dir, "server.jar")
        download_success = False
        try:
            meta_url = f"https://meta.fabricmc.net/v2/versions/loader/{version}"
            req = urllib.request.Request(meta_url, headers={"User-Agent": "mtils-cli"})
            with urllib.request.urlopen(req) as resp:
                loaders_data = json.loads(resp.read().decode())
            if loaders_data:
                loader_ver = loaders_data[0]["loader"]["version"]
                installer_ver = loaders_data[0].get("installer", {}).get("version", "1.0.1")
                launch_url = f"https://meta.fabricmc.net/v2/versions/loader/{version}/{loader_ver}/{installer_ver}/server/jar"
                download_success = download_file(launch_url, server_jar_path, f"Fabric Server {version}")
        except Exception as e:
            print(f" [!] Fabric Meta lookup failed: {e}")

        if not download_success:
            fallback_url = f"https://meta.fabricmc.net/v2/versions/loader/{version}/0.15.11/1.0.1/server/jar"
            download_file(fallback_url, server_jar_path, f"Fabric Server {version} (Fallback)")

        with open(os.path.join(target_dir, "start.bat"), "w", encoding="utf-8") as f:
            f.write("@echo off\necho [*] Starting Fabric Server...\njava -Xmx4G -Xms2G -jar server.jar nogui\npause\n")

                     
    elif loader == "forge":
        forge_build = get_forge_version(version)
        installer_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{version}-{forge_build}/forge-{version}-{forge_build}-installer.jar"
        installer_target = os.path.join(target_dir, "forge-installer.jar")
        
        print(f" [*] Downloading Forge Installer ({version}-{forge_build})...")
        download_file(installer_url, installer_target, "Forge Installer")

        with open(os.path.join(target_dir, "install_server.bat"), "w", encoding="utf-8") as f:
            f.write("@echo off\necho [*] Installing Forge Server libraries...\njava -jar forge-installer.jar --installServer\necho [+] Done! Now you can run start.bat\npause\n")

        with open(os.path.join(target_dir, "start.bat"), "w", encoding="utf-8") as f:
            f.write(f"@echo off\nif not exist run.bat (\n    echo [!] Run install_server.bat first to set up libraries!\n    pause\n    exit /b\n)\ncall run.bat\npause\n")

                      
    elif loader == "purpur":
        purpur_url = f"https://api.purpurmc.org/v2/purpur/{version}/latest/download"
        server_jar_path = os.path.join(target_dir, "server.jar")
        download_file(purpur_url, server_jar_path, f"Purpur {version}")
        with open(os.path.join(target_dir, "start.bat"), "w", encoding="utf-8") as f:
            f.write("@echo off\njava -Xmx4G -Xms2G -jar server.jar nogui\npause\n")

                     
    else:
        print(f" [*] Resolving PaperMC build for {version}...")
        try:
            api_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "mtils-cli"})
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                latest_build = data["builds"][-1]
                jar_name = f"paper-{version}-{latest_build}.jar"
                download_url = f"https://api.papermc.io/v2/projects/paper/versions/{version}/builds/{latest_build}/downloads/{jar_name}"

            server_jar_path = os.path.join(target_dir, "server.jar")
            download_file(download_url, server_jar_path, f"Paper {version} (#{latest_build})")
        except Exception as e:
            print(f" [!] Paper download error: {e}")

        with open(os.path.join(target_dir, "start.bat"), "w", encoding="utf-8") as f:
            f.write("@echo off\njava -Xmx4G -Xms2G -jar server.jar nogui\npause\n")

    show_progress(1, 2, "Accepting Minecraft EULA (eula=true)...")
    with open(os.path.join(target_dir, "eula.txt"), "w", encoding="utf-8") as f:
        f.write("eula=true\n")

    show_progress(2, 2, "Configuring server.properties...")
    with open(os.path.join(target_dir, "server.properties"), "w", encoding="utf-8") as f:
        f.write(f"online-mode=true\ndifficulty=normal\nmax-players=20\nserver-port=25565\n# mtils {loader} {version}\n")

    print(f" [+] Server ready: {target_dir}\n")

                                                               
                          
                                                               
def handle_mod_command(args, cfg):
    if not args:
        print(" [!] Usage: mod <name> <loader> <version> <lang>")
        print("     Or:    mod set <path> | mod desync | mod export")
        return

    sub = args[0].lower()

    if sub == "set":
        if len(args) < 2:
            print(" [!] Specify path: mod set <path>")
            return
        target = resolve_path(args[1])
        if not os.path.exists(target):
            print(f" [!] Path does not exist: {target}")
            return
        state["bound_mod"] = target
        print(f" [*] Mod directory bound: {target}")
        if GUI_WINDOW is not None:
            GUI_WINDOW.update_prompt_ui()
        return

    if sub == "desync":
        state["bound_mod"] = None
        print(" [*] Mod directory unbound.")
        if GUI_WINDOW is not None:
            GUI_WINDOW.update_prompt_ui()
        return

    if sub == "export":
        if not state["bound_mod"]:
            print(" [!] No mod bound to current session. Use 'mod set <path>' first.")
            return
        print(f" [*] Running build task inside: {state['bound_mod']}...")
        gradlew = "gradlew.bat" if os.name == "nt" else "./gradlew"
        target_bin = os.path.join(state["bound_mod"], gradlew)
        if os.path.exists(target_bin):
            subprocess.run([target_bin, "build"], cwd=state["bound_mod"])
            print(" [+] Build process completed.")
        else:
            print(f" [!] Build wrapper not found at {target_bin}")
        return

    name = args[0]
    loader = args[1].lower() if len(args) > 1 else "forge"
    version = args[2] if len(args) > 2 else "1.20.1"
    lang = args[3].lower() if len(args) > 3 else "java"
    target_dir = os.path.join(CREATED_DIR, "mods", name)

    if not confirm_action(f"Create IntelliJ IDEA mod workspace '{name}' ({loader} {version}, {lang}) in created/mods/?"):
        print(" [-] Operation cancelled by user.")
        return

    print(f"\n [*] Setting up Mod Workspace: {name} [{loader.upper()} {version} | {lang.upper()}]...")

    if loader == "fabric":
        zip_temp = os.path.join(CREATED_DIR, "mods", f"{name}_temp.zip")
        download_url = f"https://github.com/FabricMC/fabric-example-mod/archive/refs/heads/{version}.zip"
        print(f" [*] Fetching official Fabric MDK template from GitHub...")
        success = download_file(download_url, zip_temp, "Downloading Fabric MDK")

        if success:
            show_progress(1, 4, "Extracting MDK archive...")
            extract_temp = os.path.join(CREATED_DIR, "mods", f"{name}_raw")
            try:
                with zipfile.ZipFile(zip_temp, 'r') as zf:
                    zf.extractall(extract_temp)
                inner_dir = os.path.join(extract_temp, os.listdir(extract_temp)[0])
                if os.path.exists(target_dir):
                    shutil.rmtree(target_dir)
                shutil.move(inner_dir, target_dir)
            except Exception as e:
                print(f" [!] Extraction error: {e}")
            finally:
                if os.path.exists(zip_temp):
                    os.remove(zip_temp)
                if os.path.exists(extract_temp):
                    shutil.rmtree(extract_temp, ignore_errors=True)

            show_progress(2, 4, f"Refactoring all files and packages to '{name}'...")
            refactor_fabric_template(target_dir, name)

            show_progress(3, 4, "Verifying Gradle Wrapper...")
            if not os.path.exists(os.path.join(target_dir, "gradlew.bat")):
                generate_gradle_wrapper(target_dir)

            show_progress(4, 4, "Workspace finalized successfully.")
            print(f" [+] Fabric Mod ready: {target_dir}\n")
            return

    total_steps = 6
    show_progress(1, total_steps, "Allocating directories for IntelliJ IDEA...")
    src_dir = os.path.join(target_dir, "src", "main", "java" if lang == "java" else "kotlin", "com", "example", name.lower())
    res_meta = os.path.join(target_dir, "src", "main", "resources", "META-INF")
    res_lang = os.path.join(target_dir, "src", "main", "resources", "assets", name.lower(), "lang")
    for d in [src_dir, res_meta, res_lang]:
        os.makedirs(d, exist_ok=True)

    show_progress(2, total_steps, "Deploying Gradle Wrapper (8.5)...")
    generate_gradle_wrapper(target_dir)

    show_progress(3, total_steps, "Configuring settings.gradle with Forge Maven...")
    with open(os.path.join(target_dir, "settings.gradle"), "w", encoding="utf-8") as f:
        f.write(f"""pluginManagement {{
    repositories {{
        maven {{ url = 'https://maven.minecraftforge.net/' }}
        gradlePluginPortal()
        mavenCentral()
    }}
}}
rootProject.name = '{name.lower()}'
""")

    forge_build = get_forge_version(version)
    show_progress(4, total_steps, f"Linking Forge dependencies ({version}-{forge_build})...")
    with open(os.path.join(target_dir, "build.gradle"), "w", encoding="utf-8") as f:
        f.write(f"""plugins {{
    id 'eclipse'
    id 'idea'
    id 'net.minecraftforge.gradle' version '[6.0,6.2)'
    { "id 'org.jetbrains.kotlin.jvm' version '1.9.22'" if lang == "kotlin" else "" }
}}

group = 'com.example'
version = '1.0.0'

java {{
    toolchain.languageVersion = JavaLanguageVersion.of(17)
}}

minecraft {{
    mappings channel: 'official', version: '{version}'
}}

repositories {{
    mavenCentral()
    maven {{ url = 'https://maven.minecraftforge.net/' }}
}}

dependencies {{
    minecraft 'net.minecraftforge:forge:{version}-{forge_build}'
}}
""")

    show_progress(5, total_steps, "Writing mods.toml & starter class...")
    with open(os.path.join(res_meta, "mods.toml"), "w", encoding="utf-8") as f:
        f.write(f"""modLoader="javafml"
loaderVersion="[47,)"
license="All Rights Reserved"

[[mods]]
modId="{name.lower()}"
version="1.0.0"
displayName="{name}"
description="Generated with mtils."
""")

    ext = "kt" if lang == "kotlin" else "java"
    main_file = os.path.join(src_dir, f"{name.capitalize()}Mod.{ext}")
    with open(main_file, "w", encoding="utf-8") as f:
        if lang == "kotlin":
            f.write(f"package com.example.{name.lower()}\n\nobject {name.capitalize()}Mod {{\n    const val MOD_ID = \"{name.lower()}\"\n}}\n")
        else:
            f.write(f"package com.example.{name.lower()};\n\npublic class {name.capitalize()}Mod {{\n    public static final String MOD_ID = \"{name.lower()}\";\n}}\n")

    show_progress(6, total_steps, "Ready for IntelliJ IDEA import.")
    print(f" [+] Mod workspace successfully created: {target_dir}\n")

def handle_plugin_command(args, cfg):
    if len(args) < 1:
        print(" [!] Usage: plugin <name> [loader/platform] [version]")
        return

    name = args[0]
    platform = args[1].lower() if len(args) > 1 else "paper"
    version = args[2] if len(args) > 2 else "1.20.1"
    target_dir = os.path.join(CREATED_DIR, "plugins", name)

    if not confirm_action(f"Create {platform} plugin '{name}' ({version}) in created/plugins/?"):
        print(" [-] Operation cancelled by user.")
        return

    print(f"\n [*] Initializing Plugin: {name} [{platform.upper()} {version}]...")
    total_steps = 4

    show_progress(1, total_steps, "Allocating package structure...")
    src_dir = os.path.join(target_dir, "src", "main", "java", "com", "example", name.lower())
    res_dir = os.path.join(target_dir, "src", "main", "resources")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(res_dir, exist_ok=True)

    show_progress(2, total_steps, "Generating plugin.yml manifest...")
    with open(os.path.join(res_dir, "plugin.yml"), "w", encoding="utf-8") as f:
        f.write(f"name: {name}\nversion: 1.0.0\nmain: com.example.{name.lower()}.{name.capitalize()}Plugin\napi-version: '1.20'\nauthor: mtils\n")

    show_progress(3, total_steps, "Writing Java main plugin class...")
    with open(os.path.join(src_dir, f"{name.capitalize()}Plugin.java"), "w", encoding="utf-8") as f:
        f.write(f"package com.example.{name.lower()};\n\nimport org.bukkit.plugin.java.JavaPlugin;\n\npublic class {name.capitalize()}Plugin extends JavaPlugin {{\n    @Override\n    public void onEnable() {{\n        getLogger().info(\"{name} enabled successfully!\");\n    }}\n}}\n")

    show_progress(4, total_steps, f"Configuring build.gradle with {platform} repositories...")
    repo_url = "https://repo.papermc.io/repository/maven-public/" if platform == "paper" else "https://hub.spigotmc.org/nexus/content/repositories/snapshots/"
    dep_str = f"compileOnly 'io.papermc.paper:paper-api:{version}-R0.1-SNAPSHOT'" if platform == "paper" else f"compileOnly 'org.spigotmc:spigot-api:{version}-R0.1-SNAPSHOT'"
    
    with open(os.path.join(target_dir, "build.gradle"), "w", encoding="utf-8") as f:
        f.write(f"""plugins {{
    id 'java'
}}

group = 'com.example'
version = '1.0.0'

repositories {{
    mavenCentral()
    maven {{ url '{repo_url}' }}
}}

dependencies {{
    {dep_str}
}}

java {{
    toolchain.languageVersion = JavaLanguageVersion.of(17)
}}
""")

    with open(os.path.join(target_dir, "settings.gradle"), "w", encoding="utf-8") as f:
        f.write(f"rootProject.name = '{name.lower()}'\n")

    generate_gradle_wrapper(target_dir)
    print(f" [+] Plugin successfully created: {target_dir}\n")

def handle_respack_command(args, cfg):
    if len(args) < 1:
        print(" [!] Usage: respack <name> [version]")
        return

    name = args[0]
    version = args[1] if len(args) > 1 else "1.20.1"
    pack_format = get_pack_format(version)
    target_dir = os.path.join(CREATED_DIR, "repacks", name)

    if not confirm_action(f"Create Resource Pack '{name}' ({version} | format {pack_format}) in created/repacks/?"):
        print(" [-] Operation cancelled by user.")
        return

    print(f"\n [*] Initializing Resource Pack: {name} [MC: {version} | Format: {pack_format}]...")
    show_progress(1, 3, "Creating textures and models folder hierarchy...")
    textures_dir = os.path.join(target_dir, "assets", "minecraft", "textures")
    models_dir = os.path.join(target_dir, "assets", "minecraft", "models")
    os.makedirs(textures_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    show_progress(2, 3, "Generating pack.mcmeta...")
    mcmeta = {
        "pack": {
            "pack_format": pack_format,
            "description": f"Custom Resource Pack: {name} (mtils for {version})"
        }
    }
    with open(os.path.join(target_dir, "pack.mcmeta"), "w", encoding="utf-8") as f:
        json.dump(mcmeta, f, indent=4)

    show_progress(3, 3, "Finalizing Resource Pack...")
    print(f" [+] Resource Pack ready: {target_dir}\n")

def handle_datapack_command(args, cfg):
    if len(args) < 1:
        print(" [!] Usage: datapack <name> [version]")
        return

    name = args[0]
    version = args[1] if len(args) > 1 else "1.20.1"
    pack_format = get_pack_format(version)
    target_dir = os.path.join(CREATED_DIR, "datapacks", name)

    if not confirm_action(f"Create Datapack '{name}' ({version} | format {pack_format}) in created/datapacks/?"):
        print(" [-] Operation cancelled by user.")
        return

    print(f"\n [*] Initializing Datapack: {name} [MC: {version} | Format: {pack_format}]...")
    show_progress(1, 3, "Creating functions and tags directory...")
    fn_dir = os.path.join(target_dir, "data", name.lower(), "functions")
    tags_dir = os.path.join(target_dir, "data", "minecraft", "tags", "functions")
    os.makedirs(fn_dir, exist_ok=True)
    os.makedirs(tags_dir, exist_ok=True)

    show_progress(2, 3, "Generating pack.mcmeta...")
    mcmeta = {
        "pack": {
            "pack_format": pack_format,
            "description": f"Custom Datapack: {name} (mtils for {version})"
        }
    }
    with open(os.path.join(target_dir, "pack.mcmeta"), "w", encoding="utf-8") as f:
        json.dump(mcmeta, f, indent=4)

    show_progress(3, 3, "Writing initial main.mcfunction...")
    with open(os.path.join(fn_dir, "main.mcfunction"), "w", encoding="utf-8") as f:
        f.write(f"# Main function for {name}\ntellraw @a {{\"text\":\"[Datapack {name}] Initialized.\",\"color\":\"green\"}}\n")

    print(f" [+] Datapack ready: {target_dir}\n")

def handle_theme_install(args, cfg):
    if not args:
        print(" [!] Usage: theme install <user/repo | theme_name>")
        return

    target = args[0].strip()
    owner = None
    repo_name = None
    default_branch = "main"

    if "/" in target:
        parts = target.split("/")
        owner, repo_name = parts[0], parts[1]
        print(f" [*] Connecting directly to repository: {owner}/{repo_name}...")
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"
        req = urllib.request.Request(api_url, headers={"User-Agent": "mtils-cli"})
        try:
            with urllib.request.urlopen(req) as resp:
                repo_data = json.loads(resp.read().decode("utf-8-sig"))
            default_branch = repo_data.get("default_branch", "main")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f" [!] Repository '{target}' not found or is private.")
            else:
                print(f" [!] GitHub API error ({e.code}): {e.reason}")
            return
        except Exception as e:
            print(f" [!] Connection failed: {e}")
            return
    else:
        print(f" [*] Searching GitHub for theme '{target}'...")
        search_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(target)}+topic:mtilstheme"
        req = urllib.request.Request(search_url, headers={"User-Agent": "mtils-cli"})
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8-sig"))
            if data.get("total_count", 0) == 0:
                print(f" [!] Theme '{target}' not found in GitHub search with tag 'mtilstheme'.")
                return
            repo = data["items"][0]
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            default_branch = repo.get("default_branch", "main")
            print(f" [*] Found repository: {owner}/{repo_name}")
        except Exception as e:
            print(f" [!] Search error: {e}")
            return

    zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/{default_branch}.zip"
    zip_dest = os.path.join(THEMES_DIR, f"{repo_name}_temp.zip")
    extract_dir = os.path.join(THEMES_DIR, f"{repo_name}_temp_dir")

    print(f" [*] Downloading theme package from GitHub ({default_branch} branch)...")
    if not download_file(zip_url, zip_dest, "Theme Package"):
        print(" [!] Failed to download theme archive from GitHub.")
        return

    try:
        with zipfile.ZipFile(zip_dest, 'r') as zf:
            zf.extractall(extract_dir)

        found_settings_path = None
        settings_data = None

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                fl = file.lower()
                if fl in ["settings.json", "settings", "settings.json.txt", "settings.mutheme"]:
                    test_p = os.path.join(root, file)
                    try:
                        with open(test_p, "r", encoding="utf-8-sig") as sf:
                            parsed = json.load(sf)
                        if isinstance(parsed, dict) and all(k in parsed for k in ["name", "author", "version"]):
                            found_settings_path = test_p
                            settings_data = parsed
                            break
                    except Exception:
                        pass
            if found_settings_path:
                break

        if not settings_data or not found_settings_path:
            print(" [!] Security / Structure Error: Valid settings.json not found inside repository!")
            return

        theme_name = settings_data.get("name", repo_name).strip()
        theme_root_dir = os.path.dirname(found_settings_path)

        print(f" [+] Verified theme: '{theme_name}' by {settings_data.get('author')} (v{settings_data.get('version')})")

        final_folder = os.path.join(THEMES_DIR, theme_name)
        if os.path.exists(final_folder):
            shutil.rmtree(final_folder)

        shutil.copytree(theme_root_dir, final_folder)
        print(f" [+] Theme successfully installed to: themes/{theme_name}")
        print(f"     Type 'theme set {theme_name}' to apply it! 🎨\n")

    except Exception as e:
        print(f" [!] Installation error: {e}")
    finally:
        if os.path.exists(zip_dest):
            os.remove(zip_dest)
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)

def handle_theme_command(args, cfg):
    if not args:
        print(f" [*] Active theme: \033[93m{cfg.get('active_theme', 'default')}\033[0m")
        print(f" [*] Settings: bg={cfg.get('theme_settings', {}).get('animated_bg')}, anim={cfg.get('theme_settings', {}).get('block_anim')}, texteffect={cfg.get('theme_settings', {}).get('texteffect')}")
        print(" [!] Usage: theme list, theme set <name>, theme bg <on/off>, theme install <repo>")
        return

    action = args[0].lower()

    if action == "install":
        handle_theme_install(args[1:], cfg)
        return

    if action == "list":
        if not os.path.exists(THEMES_DIR):
            print(" [*] Themes directory is empty.")
            return
        items = os.listdir(THEMES_DIR)
        print(" [*] Available themes in /themes:")
        if not items:
            print("     (no themes found, place .zip or folder inside themes/)")
        for item in items:
            clean_name = item.replace(".zip", "")
            marker = " (ZIP)" if item.endswith(".zip") else " (Folder)"
            print(f"   - {clean_name}{marker}")
        return

    if action == "set" and len(args) > 1:
        raw_theme_name = args[1]
        target_folder_name = raw_theme_name
        zip_path = os.path.join(THEMES_DIR, f"{raw_theme_name}.zip")
        folder_path = os.path.join(THEMES_DIR, raw_theme_name)

        if os.path.exists(THEMES_DIR):
            for item in os.listdir(THEMES_DIR):
                if item.lower() == f"{raw_theme_name.lower()}.zip":
                    zip_path = os.path.join(THEMES_DIR, item)
                    target_folder_name = item.replace(".zip", "")
                    folder_path = os.path.join(THEMES_DIR, target_folder_name)
                    break
                elif item.lower() == raw_theme_name.lower():
                    target_folder_name = item
                    folder_path = os.path.join(THEMES_DIR, item)
                    break

        if os.path.exists(zip_path):
            print(f" [*] Unpacking theme archive: {os.path.basename(zip_path)}...")
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(folder_path)
                print(f" [+] Extracted into: {folder_path}")
            except Exception as e:
                print(f" [!] Failed to unpack theme: {e}")
                return

        if not os.path.exists(folder_path):
            print(f" [!] Theme folder or zip not found: {raw_theme_name}")
            return

        cfg["active_theme"] = target_folder_name
        save_config(cfg)
        print(f" [+] Active theme switched to: {target_folder_name}")
        
        global GUI_WINDOW
        if GUI_WINDOW is not None:
            GUI_WINDOW.apply_active_theme()
        return

    if action in ["bg", "anim"] and len(args) > 1:
        toggle = args[1].lower() in ["on", "true", "1"]
        key = "animated_bg" if action == "bg" else "block_anim"
        cfg["theme_settings"][key] = toggle
        save_config(cfg)
        print(f" [+] Setting '{key}' updated to: {toggle}")
        if GUI_WINDOW is not None:
            if action == "bg":
                GUI_WINDOW.reload_theme_background()
            elif action == "anim":
                GUI_WINDOW.toggle_block_animation(toggle)
        return

    print(" [!] Unknown theme argument. Type 'help' for syntax.")

def handle_texteffect_command(args, cfg):
    if not args:
        print(" [!] Usage: texteffect on/off")
        return
    toggle = args[0].lower() in ["on", "true", "1"]
    cfg.setdefault("theme_settings", {})["texteffect"] = toggle
    save_config(cfg)
    if GUI_WINDOW is not None:
        GUI_WINDOW.input_field.glitch_enabled = toggle
    print(f" [+] Text glitch effect set to: {toggle}")

def handle_alias_command(args, cfg):
    if not args:
        print(" [!] Usage: alias add <short> <command> OR alias list")
        return

    sub = args[0].lower()
    if sub == "list":
        print(" [*] Configured aliases:")
        for k, v in cfg.get("aliases", {}).items():
            print(f"   {k} -> {v}")
        return

    if sub == "add" and len(args) >= 3:
        short = args[1]
        full = " ".join(args[2:])
        cfg.setdefault("aliases", {})[short] = full
        save_config(cfg)
        print(f" [+] Alias saved: '{short}' -> '{full}'")
        return

    print(" [!] Invalid alias command syntax.")

def execute_command_line(user_input, cfg):
    user_input = user_input.strip()
    if not user_input:
        return True

    parts = user_input.split()
    cmd = parts[0]
    args = parts[1:]

    aliases = cfg.get("aliases", {})
    if cmd in aliases:
        expanded = aliases[cmd].split()
        cmd = expanded[0]
        args = expanded[1:] + args

    if cmd == "exit":
        print(" [*] Shutting down mtils...")
        return False
    elif cmd in ["clear", "cls"]:
        global GUI_WINDOW
        if GUI_WINDOW is not None:
            GUI_WINDOW.log_view.clear()
            GUI_WINDOW.print_startup_banner()
        else:
            os.system("cls" if os.name == "nt" else "clear")
    elif cmd == "help":
        print_help()
    elif cmd == "mod":
        handle_mod_command(args, cfg)
    elif cmd == "server":
        handle_server_command(args, cfg)
    elif cmd == "plugin":
        handle_plugin_command(args, cfg)
    elif cmd in ["respack", "repack"]:
        handle_respack_command(args, cfg)
    elif cmd == "datapack":
        handle_datapack_command(args, cfg)
    elif cmd == "theme":
        handle_theme_command(args, cfg)
    elif cmd == "texteffect":
        handle_texteffect_command(args, cfg)
    elif cmd == "alias":
        handle_alias_command(args, cfg)
    else:
        print(f" [!] Unknown command: '{cmd}'. Type 'help' for guidance.")
    return True

                                                               
                                                               
                                                               
try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                 QHBoxLayout, QLabel, QTextEdit, QLineEdit, QPushButton, QMessageBox)
    from PyQt6.QtCore import Qt, QUrl, QTimer, QPoint, QPointF, QRect, QEvent, QPropertyAnimation, QEasingCurve, qInstallMessageHandler
    from PyQt6.QtGui import (QFont, QTextCursor, QPainter, QColor, QPolygonF,
                             QBrush, QPixmap, QImage, QPainterPath, QTransform, QLinearGradient)
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
    PYQT_AVAILABLE = True

    def qt_silent_logger(mode, context, message):
        pass

    qInstallMessageHandler(qt_silent_logger)

except ImportError:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:

    def parse_theme_color(color_val, default=QColor(255, 255, 255)):
        if not color_val:
            return default
        if isinstance(color_val, QColor):
            return color_val
        c_str = str(color_val).strip()
        m = re.match(r"rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d\.]+)\s*\)", c_str, re.IGNORECASE)
        if m:
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            a_f = float(m.group(4))
            a = int(a_f * 255) if a_f <= 1.0 else int(a_f)
            return QColor(r, g, b, min(255, max(0, a)))
        c = QColor(c_str)
        if c.isValid():
            return c
        return default

    class AppleLiquidGlassPopup(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setFixedSize(430, 136)
            
            self.matches = []
            self.target_index = 0
            self.current_index = 0
            self.scroll_pos = 0.0

            self.accent_color = QColor(85, 255, 85)
            self.text_color = QColor(255, 255, 255)
            self.bg_tint = QColor(20, 25, 35)

            self.anim_timer = QTimer(self)
            self.anim_timer.timeout.connect(self.update_smooth_scroll)
            self.anim_timer.start(16)
            self.hide()

        def apply_theme_style(self, colors):
            self.accent_color = parse_theme_color(colors.get("border", "#55FF55"), QColor(85, 255, 85))
            self.text_color = parse_theme_color(colors.get("text", "#FFFFFF"), QColor(255, 255, 255))
            raw_bg = parse_theme_color(colors.get("input_bg", "#141823"), QColor(20, 24, 35))
            self.bg_tint = raw_bg
            self.update()

        def update_smooth_scroll(self):
            diff = self.target_index - self.scroll_pos
            if abs(diff) > 0.005:
                self.scroll_pos += diff * 0.28
                self.update()
            else:
                if self.scroll_pos != float(self.target_index):
                    self.scroll_pos = float(self.target_index)
                    self.update()

        def set_matches(self, matches):
            self.matches = matches
            self.target_index = 0
            self.current_index = 0
            self.scroll_pos = 0.0
            if matches:
                self.show()
                self.raise_()
            else:
                self.hide()
            self.update()

        def move_selection(self, delta):
            if not self.matches:
                return
            n = len(self.matches)
            old_target = self.target_index
            self.target_index = (self.target_index + delta) % n
            self.current_index = self.target_index

            if old_target == 0 and delta < 0:
                self.scroll_pos = n + 0.3
            elif old_target == n - 1 and delta > 0:
                self.scroll_pos = -1.3

            self.update()

        def get_selected(self):
            if self.matches and 0 <= self.current_index < len(self.matches):
                return self.matches[self.current_index]
            return ""

        def paintEvent(self, event):
            if not self.matches:
                return
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            w, h = self.width(), self.height()
            radius = 16.0

            body_path = QPainterPath()
            body_path.addRoundedRect(1.5, 1.5, w - 3.0, h - 3.0, radius, radius)

            glass_grad = QLinearGradient(0, 0, 0, h)
            tint_r = int(self.accent_color.red() * 0.30 + self.bg_tint.red() * 0.70)
            tint_g = int(self.accent_color.green() * 0.30 + self.bg_tint.green() * 0.70)
            tint_b = int(self.accent_color.blue() * 0.30 + self.bg_tint.blue() * 0.70)
            
            c_top = QColor(tint_r, tint_g, tint_b, 105)
            c_bot = QColor(10, 14, 22, 145)
            glass_grad.setColorAt(0.0, c_top)
            glass_grad.setColorAt(1.0, c_bot)

            painter.setBrush(QBrush(glass_grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(body_path)

            sheen_path = QPainterPath()
            sheen_path.addRoundedRect(2.0, 2.0, w - 4.0, h * 0.46, radius - 1.0, radius - 1.0)
            sheen_grad = QLinearGradient(0, 2, 0, h * 0.46)
            sheen_grad.setColorAt(0.0, QColor(255, 255, 255, 80))
            sheen_grad.setColorAt(0.6, QColor(255, 255, 255, 20))
            sheen_grad.setColorAt(1.0, QColor(255, 255, 255, 0))

            painter.setBrush(QBrush(sheen_grad))
            painter.drawPath(sheen_path)

            rim_grad = QLinearGradient(0, 0, 0, h)
            rim_grad.setColorAt(0.0, QColor(255, 255, 255, 230))
            acc_solid = QColor(self.accent_color)
            acc_solid.setAlpha(210)
            rim_grad.setColorAt(0.40, acc_solid)
            acc_bot = QColor(self.accent_color).darker(110)
            acc_bot.setAlpha(170)
            rim_grad.setColorAt(1.0, acc_bot)

            painter.setBrush(Qt.BrushStyle.NoBrush)
            pen_rim = painter.pen()
            pen_rim.setWidthF(2.0)
            pen_rim.setBrush(QBrush(rim_grad))
            painter.setPen(pen_rim)
            painter.drawPath(body_path)

            clip_path = QPainterPath()
            clip_path.addRoundedRect(3.0, 3.0, w - 6.0, h - 6.0, radius - 2.0, radius - 2.0)
            painter.setClipPath(clip_path)

            center_y = h / 2.0 - 12.0

            for i, match_text in enumerate(self.matches):
                offset = i - self.scroll_pos

                if len(self.matches) >= 5:
                    while offset > len(self.matches) / 2.0:
                        offset -= len(self.matches)
                    while offset < -len(self.matches) / 2.0:
                        offset += len(self.matches)

                slot_y = center_y + offset * 24.0
                if slot_y < -24 or slot_y > h + 12:
                    continue

                rect = QRect(8, int(slot_y), w - 16, 24)
                dist = abs(offset)

                if dist < 0.5:
                    pill_path = QPainterPath()
                    pill_path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), 8, 8)

                    pill_grad = QLinearGradient(0, rect.top(), 0, rect.bottom())
                    pill_c1 = QColor(self.accent_color.red(), self.accent_color.green(), self.accent_color.blue(), 180)
                    pill_c2 = QColor(self.accent_color.red(), self.accent_color.green(), self.accent_color.blue(), 115)
                    pill_grad.setColorAt(0.0, pill_c1)
                    pill_grad.setColorAt(1.0, pill_c2)

                    painter.setBrush(QBrush(pill_grad))
                    painter.setPen(QColor(255, 255, 255, 190))
                    painter.drawPath(pill_path)

                    painter.setPen(QColor(255, 255, 255))
                    painter.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
                    painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "  ▶  " + match_text)
                else:
                    alpha = max(35, int(190 * (1.0 - dist * 0.38)))
                    painter.setPen(QColor(240, 245, 255, alpha))
                    painter.setFont(QFont("Consolas", 10))
                    painter.drawText(rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, "     " + match_text)

    class GlitchLineEdit(QLineEdit):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.popup = None
            self.glitch_enabled = True
            self.is_glitching = False
            self.glitch_timer = QTimer(self)
            self.glitch_timer.setSingleShot(True)
            self.glitch_timer.timeout.connect(self.end_glitch)
            self.textEdited.connect(self.on_text_edited)

        def on_text_edited(self, text):
            if not text.strip():
                if self.popup:
                    self.popup.hide()
                    self.popup.set_matches([])
                return

            matches = get_contextual_suggestions(text)
            if self.popup:
                self.popup.set_matches(matches)
                self.reposition_popup()

            if self.glitch_enabled:
                self.is_glitching = True
                self.update()
                self.glitch_timer.start(45)

        def reposition_popup(self):
            if not self.popup or not self.popup.isVisible():
                return
            p = self.mapTo(self.window().central_widget, QPoint(0, 0))
            w = 430
            h = 136
            x = p.x() + 8
            y = p.y() - h - 4
            self.popup.setGeometry(x, y, w, h)
            self.popup.raise_()

        def end_glitch(self):
            self.is_glitching = False
            self.update()

        def paintEvent(self, event):
            super().paintEvent(event)
            if self.is_glitching and self.text():
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                fm = self.fontMetrics()
                txt = self.text()
                tw = fm.horizontalAdvance(txt)
                last_w = fm.horizontalAdvance(txt[-1])
                x = 14 + tw - last_w
                y = (self.height() + fm.ascent() - fm.descent()) // 2
                painter.setPen(QColor(255, 105, 180, 240))
                painter.setFont(self.font())
                painter.drawText(x, y, random.choice("!@#$<>?%*~"))
                painter.end()

        def event(self, event):
            if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Tab:
                if self.popup and self.popup.isVisible():
                    comp = self.popup.get_selected()
                    if comp:
                        self.setText(comp + " ")
                        self.on_text_edited(self.text())
                        return True
                else:
                    matches = get_contextual_suggestions(self.text())
                    if matches:
                        self.setText(matches[0] + " ")
                        self.on_text_edited(self.text())
                        return True
            return super().event(event)

        def keyPressEvent(self, event):
            if self.popup and self.popup.isVisible():
                if event.key() == Qt.Key.Key_Up:
                    self.popup.move_selection(-1)
                    return
                elif event.key() == Qt.Key.Key_Down:
                    self.popup.move_selection(1)
                    return
                elif event.key() in [Qt.Key.Key_Escape, Qt.Key.Key_Return]:
                    self.popup.hide()
            super().keyPressEvent(event)

        def hideEvent(self, event):
            if self.popup:
                self.popup.hide()
            super().hideEvent(event)

    class CustomTitleBar(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.parent_window = parent
            self.drag_position = QPoint()
            self.setFixedHeight(34)

            layout = QHBoxLayout(self)
            layout.setContentsMargins(12, 0, 8, 0)
            layout.setSpacing(8)

            self.title_icon = QLabel("🧊", self)
            self.title_label = QLabel("mtils Terminal", self)
            self.title_label.setFont(QFont("Consolas", 10, QFont.Weight.Bold))

            layout.addWidget(self.title_icon)
            layout.addWidget(self.title_label)
            layout.addStretch()

            self.btn_min = QPushButton("—", self)
            self.btn_max = QPushButton("▢", self)
            self.btn_close = QPushButton("✕", self)

            for btn in [self.btn_min, self.btn_max, self.btn_close]:
                btn.setFixedSize(30, 24)
                btn.setFont(QFont("Consolas", 10))
                layout.addWidget(btn)

            self.btn_min.clicked.connect(self.parent_window.showMinimized)
            self.btn_max.clicked.connect(self.toggle_maximize)
            self.btn_close.clicked.connect(self.parent_window.close)

        def toggle_maximize(self):
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
            else:
                self.parent_window.showMaximized()

        def mousePressEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.drag_position = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(self, event):
            if event.buttons() == Qt.MouseButton.LeftButton and not self.parent_window.isMaximized():
                self.parent_window.move(event.globalPosition().toPoint() - self.drag_position)
                event.accept()

        def apply_theme_style(self, theme_name, colors):
            text_color = colors.get("text", "#55FF55")
            border_raw = colors.get("border", "rgba(85, 255, 85, 0.35)")
            border_q = parse_theme_color(border_raw, QColor(85, 255, 85))
            
            self.title_label.setText(f"mtils Terminal - [{theme_name.capitalize()}]")
            self.title_label.setStyleSheet(f"color: {text_color}; background: transparent;")
            self.title_icon.setStyleSheet("background: transparent;")

            self.setStyleSheet(f"""
                CustomTitleBar {{
                    background-color: rgba(14, 18, 28, 0.50);
                    border-bottom: 1.8px solid rgba({border_q.red()}, {border_q.green()}, {border_q.blue()}, 0.60);
                }}
                QPushButton {{
                    background-color: transparent;
                    color: {text_color};
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 255, 255, 0.15);
                }}
            """)
            self.btn_close.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {text_color};
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: rgba(255, 50, 50, 0.75);
                    color: #FFFFFF;
                }}
            """)

    class RotatingBlockWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setFixedSize(170, 170)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.yaw = 0.0
            self.pitch = 0.52
            self.rotation_speed = 0.035

            self.top_texture = None
            self.side_texture = None
            self.bottom_texture = None

            self.create_default_grass_textures()

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_angle)
            self.timer.start(25)

        def prepare_pixel_texture(self, pixmap, target_size=256):
            if not pixmap or pixmap.isNull():
                return pixmap
            return pixmap.scaled(
                target_size,
                target_size,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation
            )

        def create_default_grass_textures(self):
            top_img = QImage(16, 16, QImage.Format.Format_RGB32)
            grass_palette = [QColor(92, 142, 50), QColor(85, 134, 45), QColor(100, 153, 55), QColor(78, 125, 40)]
            for y in range(16):
                for x in range(16):
                    c = grass_palette[(x * 7 + y * 13 + (x ^ y)) % len(grass_palette)]
                    top_img.setPixelColor(x, y, c)
            self.default_top = self.prepare_pixel_texture(QPixmap.fromImage(top_img))

            side_img = QImage(16, 16, QImage.Format.Format_RGB32)
            dirt_palette = [QColor(134, 96, 67), QColor(115, 84, 56), QColor(95, 70, 46), QColor(122, 88, 60)]
            for y in range(16):
                for x in range(16):
                    c = dirt_palette[(x * 5 + y * 11 + (x + y)) % len(dirt_palette)]
                    side_img.setPixelColor(x, y, c)

            cutoffs = [3, 4, 3, 5, 4, 3, 4, 5, 3, 4, 3, 4, 5, 4, 3, 4]
            for x in range(16):
                for y in range(cutoffs[x]):
                    c = grass_palette[(x * 3 + y * 7) % len(grass_palette)]
                    side_img.setPixelColor(x, y, c)
            self.default_side = self.prepare_pixel_texture(QPixmap.fromImage(side_img))

            bottom_img = QImage(16, 16, QImage.Format.Format_RGB32)
            for y in range(16):
                for x in range(16):
                    c = dirt_palette[(x * 9 + y * 3) % len(dirt_palette)]
                    bottom_img.setPixelColor(x, y, c)
            self.default_bottom = self.prepare_pixel_texture(QPixmap.fromImage(bottom_img))

            self.top_texture = self.default_top
            self.side_texture = self.default_side
            self.bottom_texture = self.default_bottom

        def load_theme_textures(self, theme_folder, block_cfg=None):
            self.top_texture = None
            self.side_texture = None
            self.bottom_texture = None

            if block_cfg and isinstance(block_cfg, dict):
                self.rotation_speed = block_cfg.get("speed", 0.035)
                if "top" in block_cfg:
                    p = os.path.join(theme_folder, block_cfg["top"])
                    if os.path.exists(p):
                        self.top_texture = self.prepare_pixel_texture(QPixmap(p))
                if "side" in block_cfg:
                    p = os.path.join(theme_folder, block_cfg["side"])
                    if os.path.exists(p):
                        self.side_texture = self.prepare_pixel_texture(QPixmap(p))
                if "bottom" in block_cfg:
                    p = os.path.join(theme_folder, block_cfg["bottom"])
                    if os.path.exists(p):
                        self.bottom_texture = self.prepare_pixel_texture(QPixmap(p))

            assets_dir = os.path.join(theme_folder, "assets")
            if os.path.exists(assets_dir):
                all_pngs = [f for f in os.listdir(assets_dir) if f.lower().endswith(".png")]
                if not self.top_texture:
                    for cand in ["grass_block_top.png", "block_top.png", "top.png", "nylium_top.png", "netherrack.png"]:
                        p = os.path.join(assets_dir, cand)
                        if os.path.exists(p):
                            self.top_texture = self.prepare_pixel_texture(QPixmap(p))
                            break

                if not self.side_texture:
                    for cand in ["grass_block_side.png", "block_side.png", "side.png", "netherrack.png"]:
                        p = os.path.join(assets_dir, cand)
                        if os.path.exists(p):
                            self.side_texture = self.prepare_pixel_texture(QPixmap(p))
                            break

                if not self.bottom_texture:
                    for cand in ["dirt.png", "grass_block_bottom.png", "block_bottom.png", "bottom.png", "netherrack.png"]:
                        p = os.path.join(assets_dir, cand)
                        if os.path.exists(p):
                            self.bottom_texture = self.prepare_pixel_texture(QPixmap(p))
                            break

                if not self.top_texture and all_pngs:
                    single_tex = self.prepare_pixel_texture(QPixmap(os.path.join(assets_dir, all_pngs[0])))
                    self.top_texture = single_tex
                    self.side_texture = single_tex
                    self.bottom_texture = single_tex

            if not self.top_texture:
                self.top_texture = self.default_top
            if not self.side_texture:
                self.side_texture = self.default_side
            if not self.bottom_texture:
                self.bottom_texture = self.default_bottom

            self.update()

        def update_angle(self):
            self.yaw += self.rotation_speed
            if self.yaw > 2 * math.pi:
                self.yaw -= 2 * math.pi
            self.update()

        def draw_textured_face(self, painter, proj, indices, pixmap, shade_alpha=0):
            if not pixmap or pixmap.isNull():
                return

            p0 = QPointF(proj[indices[0]][0], proj[indices[0]][1])
            p1 = QPointF(proj[indices[1]][0], proj[indices[1]][1])
            p2 = QPointF(proj[indices[2]][0], proj[indices[2]][1])
            p3 = QPointF(proj[indices[3]][0], proj[indices[3]][1])

            poly = QPolygonF([p0, p1, p2, p3])

            src_poly = QPolygonF([
                QPointF(0.0, 0.0),
                QPointF(float(pixmap.width()), 0.0),
                QPointF(float(pixmap.width()), float(pixmap.height())),
                QPointF(0.0, float(pixmap.height()))
            ])

            transform = QTransform()
            success = QTransform.quadToQuad(src_poly, poly, transform)
            if success:
                painter.save()
                path = QPainterPath()
                path.addPolygon(poly)
                painter.setClipPath(path)
                painter.setTransform(transform, True)
                painter.drawPixmap(0, 0, pixmap)
                painter.restore()

            if shade_alpha > 0:
                painter.save()
                painter.setBrush(QBrush(QColor(0, 0, 0, shade_alpha)))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPolygon(poly)
                painter.restore()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

            cx = self.width() / 2.0
            cy = self.height() / 2.0 + 8.0
            size = 48.0

            raw_vertices = [
                (-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1),
                (-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)
            ]

            proj = []
            for (x, y, z) in raw_vertices:
                x *= size
                y *= size
                z *= size

                x1 = x * math.cos(self.yaw) - z * math.sin(self.yaw)
                z1 = x * math.sin(self.yaw) + z * math.cos(self.yaw)
                y1 = y

                y2 = y1 * math.cos(self.pitch) - z1 * math.sin(self.pitch)
                z2 = y1 * math.sin(self.pitch) + z1 * math.cos(self.pitch)
                x2 = x1

                px = cx + x2
                py = cy - y2
                proj.append((px, py, z2))

            side_faces = [
                ([0, 1, 5, 4], (0, 0, -1), 40),
                ([1, 2, 6, 5], (1, 0, 0), 15),
                ([2, 3, 7, 6], (0, 0, 1), 50),
                ([3, 0, 4, 7], (-1, 0, 0), 75)
            ]

            for indices, normal, shade in side_faces:
                nx = normal[0] * math.cos(self.yaw) - normal[2] * math.sin(self.yaw)
                nz = normal[0] * math.sin(self.yaw) + normal[2] * math.cos(self.yaw)
                ny = normal[1]

                normal_z_view = ny * math.sin(self.pitch) + nz * math.cos(self.pitch)

                if normal_z_view > 0:
                    self.draw_textured_face(painter, proj, indices, self.side_texture, shade)

            self.draw_textured_face(painter, proj, [0, 1, 2, 3], self.top_texture, shade_alpha=0)

            painter.setPen(QColor(30, 30, 30, 80))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for indices, normal, _ in side_faces:
                nx = normal[0] * math.cos(self.yaw) - normal[2] * math.sin(self.yaw)
                nz = normal[0] * math.sin(self.yaw) + normal[2] * math.cos(self.yaw)
                ny = normal[1]
                if (ny * math.sin(self.pitch) + nz * math.cos(self.pitch)) > 0:
                    poly = QPolygonF([QPointF(proj[i][0], proj[i][1]) for i in indices])
                    painter.drawPolygon(poly)
            painter.drawPolygon(QPolygonF([QPointF(proj[i][0], proj[i][1]) for i in [0, 1, 2, 3]]))

            painter.end()

    class SmoothStreamRedirector:
        def __init__(self, text_widget):
            self.text_widget = text_widget
            self.queue = ""
            self.timer = QTimer()
            self.timer.setInterval(6)
            self.timer.timeout.connect(self.drain_queue)

        def write(self, text):
            if not text:
                return
            clean_text = ANSI_REGEX.sub("", text)
            self.queue += clean_text
            if not self.timer.isActive():
                self.timer.start()

        def drain_queue(self):
            if not self.queue:
                self.timer.stop()
                return

            q_len = len(self.queue)
            if q_len < 40:
                step = 1
            elif q_len < 160:
                step = 2
            elif q_len < 500:
                step = 5
            else:
                step = 16

            chunk = self.queue[:step]
            self.queue = self.queue[step:]

            cursor = self.text_widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(chunk)
            self.text_widget.setTextCursor(cursor)
            self.text_widget.ensureCursorVisible()

        def flush(self):
            while self.queue:
                self.drain_queue()

    class CustomTerminalWindow(QMainWindow):
        def __init__(self, cfg):
            super().__init__()
            self.cfg = cfg
            self.bg_pixmap = None

            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
            self.resize(1020, 670)

            self.setWindowOpacity(0.0)
            self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
            self.fade_anim.setDuration(300)
            self.fade_anim.setStartValue(0.0)
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.fade_anim.start()

            self.central_widget = QWidget(self)
            self.setCentralWidget(self.central_widget)
            self.central_widget.paintEvent = self.paint_background_video

            self.audio_output = QAudioOutput(self)
            self.audio_output.setMuted(True)
            self.media_player = QMediaPlayer(self)
            self.media_player.setAudioOutput(self.audio_output)
            self.video_sink = QVideoSink(self)
            self.media_player.setVideoSink(self.video_sink)
            self.media_player.setLoops(QMediaPlayer.Loops.Infinite)
            self.video_sink.videoFrameChanged.connect(self.on_video_frame)

            self.main_layout = QVBoxLayout(self.central_widget)
            self.main_layout.setContentsMargins(0, 0, 0, 0)
            self.main_layout.setSpacing(0)

            self.custom_titlebar = CustomTitleBar(self)
            self.main_layout.addWidget(self.custom_titlebar)

            self.content_widget = QWidget(self.central_widget)
            self.content_layout = QVBoxLayout(self.content_widget)
            self.content_layout.setContentsMargins(16, 12, 16, 16)
            self.content_layout.setSpacing(10)

            self.top_bar = QHBoxLayout()
            self.theme_badge = QLabel(self.content_widget)
            self.top_bar.addWidget(self.theme_badge)
            self.top_bar.addStretch()
            self.content_layout.addLayout(self.top_bar)

            self.log_view = QTextEdit(self.content_widget)
            self.log_view.setReadOnly(True)
            self.log_view.setFont(QFont("Consolas", 11))
            self.content_layout.addWidget(self.log_view)

            self.input_field = GlitchLineEdit(self.content_widget)
            self.input_field.setFont(QFont("Consolas", 12))
            self.input_field.glitch_enabled = self.cfg.get("theme_settings", {}).get("texteffect", True)
            self.input_field.returnPressed.connect(self.on_submit_command)
            self.content_layout.addWidget(self.input_field)

            self.main_layout.addWidget(self.content_widget)

            self.popup_menu = AppleLiquidGlassPopup(self.central_widget)
            self.input_field.popup = self.popup_menu

            self.block_widget = RotatingBlockWidget(self.central_widget)
            if not self.cfg.get("theme_settings", {}).get("block_anim", True):
                self.block_widget.hide()

            self.redirector = SmoothStreamRedirector(self.log_view)
            sys.stdout = self.redirector

            self.apply_active_theme()
            self.print_startup_banner()
            self.input_field.setFocus()

                                                     
            start_theme_scanner_thread()

        def changeEvent(self, event):
            if event.type() == QEvent.Type.WindowStateChange:
                if self.isMinimized() and hasattr(self, 'popup_menu'):
                    self.popup_menu.hide()
            super().changeEvent(event)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            w = self.central_widget.width()
            self.block_widget.setGeometry(w - 185, 48, 170, 170)
            self.block_widget.raise_()
            if hasattr(self, 'input_field'):
                self.input_field.reposition_popup()

        def update_prompt_ui(self):
            p = get_current_prompt(self.cfg)
            self.input_field.setPlaceholderText(f"{p}> Enter command here... (try 'help')")

        def apply_active_theme(self):
            theme_name = self.cfg.get("active_theme", "default")
            theme_folder = os.path.join(THEMES_DIR, theme_name)
            theme_data = {}

            for candidate in ["settings", "settings.json", "settings.mutheme"]:
                p = os.path.join(theme_folder, candidate)
                if os.path.exists(p):
                    try:
                        with open(p, "r", encoding="utf-8") as sf:
                            theme_data = json.load(sf)
                    except Exception:
                        pass
                    break

            colors = theme_data.get("colors", {})
            text_color = colors.get("text", "#55FF55")
            border_q = parse_theme_color(colors.get("border", "#55FF55"), QColor(85, 255, 85))
            focus_color = colors.get("focus", "#FFFF55")

            self.custom_titlebar.apply_theme_style(theme_name, colors)
            self.popup_menu.apply_theme_style(colors)

            self.theme_badge.setText(f"  ● ACTIVE THEME: {theme_name.upper()}  ")
            self.theme_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba({border_q.red()}, {border_q.green()}, {border_q.blue()}, 0.20);
                    color: {text_color};
                    border: 1.5px solid rgba({border_q.red()}, {border_q.green()}, {border_q.blue()}, 0.85);
                    border-radius: 9px;
                    padding: 6px 14px;
                    font-family: Consolas;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)

            self.log_view.setStyleSheet(f"""
                QTextEdit {{
                    background-color: rgba(10, 14, 22, 0.45);
                    color: {text_color};
                    border: 1.8px solid rgba({border_q.red()}, {border_q.green()}, {border_q.blue()}, 0.65);
                    border-radius: 14px;
                    padding: 14px;
                    padding-right: 185px;
                }}
                QScrollBar:vertical {{
                    border: none;
                    background: rgba(0, 0, 0, 0.15);
                    width: 7px;
                    margin: 0px;
                    border-radius: 3px;
                }}
                QScrollBar::handle:vertical {{
                    background: rgba({border_q.red()}, {border_q.green()}, {border_q.blue()}, 0.50);
                    min-height: 25px;
                    border-radius: 3px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {text_color};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    border: none;
                    background: none;
                    height: 0px;
                }}
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: none;
                }}
            """)

            self.input_field.setStyleSheet(f"""
                QLineEdit {{
                    background-color: rgba(14, 18, 28, 0.50);
                    color: #FFFFFF;
                    border: 2px solid rgba({border_q.red()}, {border_q.green()}, {border_q.blue()}, 0.70);
                    border-radius: 12px;
                    padding: 9px 14px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {focus_color};
                    background-color: rgba(18, 24, 38, 0.65);
                }}
            """)

            self.update_prompt_ui()
            self.reload_theme_background()
            self.reload_theme_block()

        def on_video_frame(self, frame):
            if frame.isValid():
                img = frame.toImage()
                if not img.isNull():
                    self.bg_pixmap = QPixmap.fromImage(img)
                    self.central_widget.update()

        def paint_background_video(self, event):
            painter = QPainter(self.central_widget)
            if self.bg_pixmap and not self.bg_pixmap.isNull() and self.cfg.get("theme_settings", {}).get("animated_bg", True):
                scaled = self.bg_pixmap.scaled(
                    self.central_widget.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.FastTransformation
                )
                x = (self.central_widget.width() - scaled.width()) // 2
                y = (self.central_widget.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
            else:
                painter.fillRect(self.central_widget.rect(), QColor("#0c0e14"))

        def print_startup_banner(self):
            banner = r"""
  __  __ _____ _____ _      _____ 
 |  \/  |_   _|_   _| |    / ____|
 | \  / | | |   | | | |   | (___  
 | |\/| | | |   | | | |    \___ \ 
 | |  | | | |   | | | |________) |
 |_|  |_| |_|   |_| |______|_____/ 
   Minecraft Developer Utilities (GUI Terminal)
"""
            print(banner)
            print(f"Working Directory: {BASE_DIR}")
            print(f"Created Projects:  {CREATED_DIR}")
            print("Type 'help' to view available commands.\n")

        def reload_theme_background(self):
            theme_name = self.cfg.get("active_theme", "default")
            theme_folder = os.path.join(THEMES_DIR, theme_name)
            bg_video_path = os.path.join(theme_folder, "assets", "bg.mp4")

            self.bg_pixmap = None
            self.media_player.stop()

            if not os.path.exists(bg_video_path) and os.path.exists(THEMES_DIR):
                for f in os.listdir(THEMES_DIR):
                    if f.lower() == theme_name.lower():
                        test_path = os.path.join(THEMES_DIR, f, "assets", "bg.mp4")
                        if os.path.exists(test_path):
                            bg_video_path = test_path
                            break

            if self.cfg.get("theme_settings", {}).get("animated_bg", True) and os.path.exists(bg_video_path):
                self.media_player.setSource(QUrl.fromLocalFile(os.path.abspath(bg_video_path)))
                self.media_player.play()
                print(f" [*] Background video loaded: {bg_video_path}")
            else:
                self.central_widget.update()

            self.block_widget.raise_()

        def reload_theme_block(self):
            theme_name = self.cfg.get("active_theme", "default")
            theme_folder = os.path.join(THEMES_DIR, theme_name)

            block_cfg = None
            for candidate in ["settings", "settings.json", "settings.mutheme"]:
                p = os.path.join(theme_folder, candidate)
                if os.path.exists(p):
                    try:
                        with open(p, "r", encoding="utf-8") as sf:
                            parsed = json.load(sf)
                            block_cfg = parsed.get("block", None)
                    except Exception:
                        pass
                    break

            self.block_widget.load_theme_textures(theme_folder, block_cfg)

        def toggle_block_animation(self, enabled):
            if enabled:
                self.block_widget.show()
                self.block_widget.raise_()
            else:
                self.block_widget.hide()

        def ask_confirmation(self, prompt_message):
            reply = QMessageBox.question(self, "mtils Confirmation", prompt_message,
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            return reply == QMessageBox.StandardButton.Yes

        def on_submit_command(self):
            raw_text = self.input_field.text().strip()
            if not raw_text:
                return

            prefix = get_current_prompt(self.cfg)
            print(f"{prefix}> {raw_text}")
            
            if self.popup_menu:
                self.popup_menu.hide()
            self.input_field.clear()

            should_continue = execute_command_line(raw_text, self.cfg)
            if not should_continue:
                self.close()

                                                               
                
                                                               
def main():
    init_environment()
    cfg = load_config()

    if PYQT_AVAILABLE:
        app = QApplication(sys.argv)
        global GUI_WINDOW
        GUI_WINDOW = CustomTerminalWindow(cfg)
        GUI_WINDOW.show()
        sys.exit(app.exec())
    else:
        print(" [!] PyQt6 is not available. Please install it using: pip install PyQt6")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()