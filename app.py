import flet as ft
from plugin_manager import PluginManager
from my_key_manager import MyKeyManager
from ui_component_manager import UIComponentManager
from ui_components.password_dialog import PasswordDialog
from ui_components.delete_confirm_dialog import DeleteConfirmDialog
from ui_components.simple_header import SimpleHeader
from ui_components.simple_footer import SimpleFooter
from ui_components.app_container import AppContainer

class CraftForgeBase:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "ChatGPT minimal starter kit"
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        self.ui_manager = UIComponentManager()
        self.ui_manager.add_component("password_daialog", PasswordDialog)
        self.ui_manager.add_component("delete_confirm_daialog", DeleteConfirmDialog)
        self.ui_manager.add_component("simple_header", SimpleHeader)
        self.ui_manager.add_component("simple_footer", SimpleFooter)
        self.ui_manager.add_component("app_container", AppContainer)
        self.mkm = MyKeyManager(self.page, self.ui_manager)
        self.pm = PluginManager(self.page, self.page_back, self.ui_manager)
        self.mkm.load_my_key()

    def show_main_page(self) -> None:
        def pick_file_and_install(e: ft.FilePickerResultEvent):
            self.pm.install_plugin(e, main_container)

        my_header_cmp = self.ui_manager.get_component("simple_header")
        my_header_instance = my_header_cmp(ft.icons.MENU_ROUNDED, "CraftForge v.0.0.1", "#20b2aa")
        my_header_widget = my_header_instance.get_widget()
        my_footer_cmp = self.ui_manager.get_component("simple_footer")
        my_footer_instance = my_footer_cmp("@hamatz", "#20b2aa")
        my_footer_widget = my_footer_instance.get_widget()
        self.page.add(my_header_widget)
        main_container = ft.GridView(
            expand=1,
            runs_count=5,
            max_extent=120,
            child_aspect_ratio=1.0,
            spacing=5,
            run_spacing=5,
        )
        self.page.add(main_container)
        self.pm.load_installed_plugins(main_container)
        # プラグインをインストールするボタンを表示する
        file_picker = ft.FilePicker(on_result=pick_file_and_install)
        self.page.overlay.append(file_picker)
        install_button = ft.ElevatedButton("Install Plugin", icon=ft.icons.UPLOAD_FILE, on_click=lambda _:file_picker.pick_files())
        self.page.add(install_button, my_footer_widget)
        self.page.update()

    def page_back(self) -> None:
        self.page.clean()
        self.show_main_page()

def main(page: ft.Page) -> None:
    app = CraftForgeBase(page)
    app.show_main_page()

if __name__ == "__main__":
    ft.app(target=main)

