import base64
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from flet.security import encrypt, decrypt
import os
import uuid
import json
import flet as ft

class MyKeyManager:

    def __init__(self, page: ft.Page, ui_manager, base_dir, my_key_file_name):
          self.__my_key_file_path = os.path.join(base_dir, my_key_file_name)
          self.__my_app_key = None
          self.__my_pass_phrase = None
          self.__page = page
          self.__ui_manager = ui_manager

    def __compute_hash(self, data) -> str:
        return hashlib.sha256(data).hexdigest()
    
    def __compare_key_and_hash(self, target, hash_value) -> bool:
        target_hash = self.__compute_hash(target)
        if target_hash == hash_value:
            return True
        else:
            return  False

    def __generate_my_key(self, user_input: str) -> None:
        password = user_input.encode()
        self.__my_pass_phrase = str(uuid.uuid4())

        salt = os.urandom(16) 
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        self.__my_app_key = kdf.derive(password)
        self.__save_my_key(salt)

    def __save_my_key(self, salt) -> None:
        # パスフレーズを暗号化
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.__my_app_key), modes.CFB(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_pass_phrase = encryptor.update(self.__my_pass_phrase.encode()) + encryptor.finalize()
        content_key_hash = self.__compute_hash(self.__my_pass_phrase.encode()).encode()
        my_appkey_settings = {
            'salt': base64.b64encode(salt).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            "encrypted_content_key": base64.b64encode(encrypted_pass_phrase).decode('utf-8'),
            "content_key_hash": base64.b64encode(content_key_hash).decode('utf-8'),
        }
        with open(self.__my_key_file_path, 'w') as f:
            json.dump(my_appkey_settings, f, indent=4)

    def load_my_key(self) -> bool:
        is_key_file = os.path.isfile(self.__my_key_file_path)
        password = None

        def close_dlg(e):
            self.__page.dialog.open = False
            self.__page.update()
            handle_key_file()

        def textbox_changed(e):
            nonlocal password
            password= e.control.value
            self.__page.update()

        dlg_component = self.__ui_manager.get_component("password_daialog")
        dlg_modal = dlg_component("起動用パスワードの入力をお願いします", "Your Password", textbox_changed, "入力完了", close_dlg)

        def open_dlg_modal():
            self.__page.dialog = dlg_modal.get_widget()
            self.__page.dialog.open = True
            self.__page.update()

        open_dlg_modal()

        def handle_key_file():
            if is_key_file:
                with open(self.__my_key_file_path, 'rb') as f:
                    data = json.load(f)
                    salt = base64.b64decode(data['salt'])
                    iv = base64.b64decode(data['iv'])
                    encrypted_pass_phrase = base64.b64decode(data['encrypted_content_key'])
                    content_key_hash = base64.b64decode(data['content_key_hash']).decode()

                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=salt,
                        iterations=100000,
                        backend=default_backend()
                    )
                self.__my_app_key = kdf.derive(password.encode())

                cipher = Cipher(algorithms.AES(self.__my_app_key), modes.CFB(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                decrypted_pass_phrase = decryptor.update(encrypted_pass_phrase) + decryptor.finalize()
                decrypted_pass_phrase_str = decrypted_pass_phrase
                check_result = self.__compare_key_and_hash(decrypted_pass_phrase_str, content_key_hash)
                if check_result:
                    self.__my_pass_phrase = decrypted_pass_phrase.decode()
                    print("app key was successfully decrypted")
                    return True
                else:
                    #パスワード間違ってるので再入力をお願いするか、あるいは設定ファイル消して最初からやるのを勧めるか...
                    print("password error")
                    return False
            else:
                print("cannot find my_app_info.json")
                self.__generate_my_key(password)

    def encrypt_data(self, target: str) -> str:
        return encrypt(target, self.__my_pass_phrase)
    
    def decrypt_data(self, target: str) -> str:
        return decrypt(target, self.__my_pass_phrase)