import base64
import zipfile
import os
import sys
import shutil
import json
import importlib
import flet as ft

PLUGIN_FOLDER = "installed_plugins"
TEMP_WORK_FOLDER = "temp"

class PluginManager:

    def __init__(self, page: ft.Page, page_back):
        self.page = page
        self.page_back_func = page_back
        if not os.path.exists(PLUGIN_FOLDER):
            os.makedirs(PLUGIN_FOLDER)
        if not os.path.exists(TEMP_WORK_FOLDER):
            os.makedirs(TEMP_WORK_FOLDER)

    def install_plugin(self, e: ft.FilePickerResultEvent) -> None:
        # プラグインを保存する一意のディレクトリを作成
        picked_file = e.files[0]
        picked_file_path = picked_file.path
        plugin_dir = os.path.join(PLUGIN_FOLDER, picked_file.name[:-4])  # ".zip"拡張子を除去
        os.makedirs(plugin_dir, exist_ok=True)
        # ZIPファイルを一時ディレクトリに保存
        zip_path = os.path.join("temp", picked_file.name)
        shutil.copy(picked_file_path, zip_path)
        # ZIPファイルを解凍するディレクトリを指定
        extract_dir = os.path.join(PLUGIN_FOLDER, picked_file.name[:-4])
        # ZIPファイルを解凍
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        # メタデータファイルを読み込み（例えば "plugin.json"）
        with open(os.path.join(extract_dir, "plugin.json"), 'r') as f:
            plugin_info = json.load(f)
        print(plugin_info)
        sys.path.append(extract_dir)
        # プラグインモジュールを動的にインポート
        plugin_module = importlib.import_module(plugin_info["main_module"])
        print(plugin_module)
        icon_path = os.path.join(extract_dir, plugin_info["icon"])
        with open(icon_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        # アプリケーションのアイコンをUIに追加 
        app_icon = ft.Image(src_base64=encoded_string, width=100, height=100)
        # アイコンのクリックイベントにプラグインのUIビルド関数を関連付け
        clickable_image = ft.GestureDetector(
            content=app_icon,
            on_tap= lambda _: plugin_module.build_ui(self.page, self.page_back_func)
        )
        #app_icon.on_click = lambda e: plugin_module.build_ui(self.page)
        # 削除ボタンの追加
        delete_button = ft.IconButton(icon=ft.icons.DELETE, on_click=lambda e: self.show_delete_confirmation(plugin_dir, [clickable_image, delete_button]))
        self.page.controls.extend([clickable_image, delete_button])
        self.page.update()

    def show_delete_confirmation(self, plugin_dir, ui_elements) -> None:

        def close_dlg(e) -> None:
            dialog.open = False
            self.page.update()
        # 削除確認ダイアログのUIを構築
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("プラグインの削除"),
            content=ft.Text("このプラグインを削除してもよろしいですか？"),
            actions=[
                ft.TextButton("いいえ", on_click=lambda e: close_dlg(e)),
                ft.TextButton("はい", on_click=lambda e: self.delete_plugin(plugin_dir, ui_elements, dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def delete_plugin(self, plugin_dir, ui_elements, dialog) -> None:

        def on_rm_error(func, path, exc_info) -> None:
            import stat
            os.chmod(path, stat.S_IWRITE)
            os.unlink(path)

        # プラグインディレクトリを削除
        shutil.rmtree(plugin_dir, onerror=on_rm_error)
        # UIからプラグイン関連の要素を削除
        for element in ui_elements:
            self.page.controls.remove(element)
        # 削除確認ダイアログを閉じる
        dialog.open = False
        self.page.update()

    def load_installed_plugins(self) -> None:
        for plugin_name in os.listdir(PLUGIN_FOLDER):
            plugin_dir = os.path.join(PLUGIN_FOLDER, plugin_name)
            if os.path.isdir(plugin_dir):
                # プラグインのメタデータを読み込み
                with open(os.path.join(plugin_dir, "plugin.json"), 'r') as f:
                    plugin_info = json.load(f)
                # アプリケーションのアイコンをUIに追加
                #icon = ft.File.from_file_path(os.path.join(plugin_dir, plugin_info["icon"]))
                sys.path.append(plugin_dir)
                # プラグインモジュールを動的にインポート
                plugin_module = importlib.import_module(plugin_info["main_module"])
                icon_path = os.path.join(plugin_dir, plugin_info["icon"])
                with open(icon_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                # アプリケーションのアイコンをUIに追加 
                app_icon = ft.Image(src_base64=encoded_string, width=100, height=100)
                # アイコンのクリックイベントにプラグインのUIビルド関数を関連付け
                clickable_image = ft.GestureDetector(
                    content=app_icon,
                    on_tap= lambda _: plugin_module.build_ui(self.page, self.page_back_func)
                )
                # 削除ボタンとアイコンのUI要素を保持するリスト
                ui_elements = [clickable_image]
                # 削除ボタンの追加
                delete_button = ft.IconButton(icon=ft.icons.DELETE, on_click=lambda e: self.show_delete_confirmation(plugin_dir, ui_elements))
                ui_elements.append(delete_button)
                self.page.controls.extend(ui_elements)

        self.page.update()
