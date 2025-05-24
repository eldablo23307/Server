#!/usr/bin/env python3
import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.utils import platform

import json
import os
from functools import partial

kivy.require('2.0.0')

class FileItem(BoxLayout):
    """Widget per rappresentare un file o directory"""
    
    def __init__(self, file_info, app_instance, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = '48dp'
        self.spacing = '10dp'
        self.padding = '10dp'
        
        self.file_info = file_info
        self.app_instance = app_instance
        
        # Icona (emoji per semplicità)
        icon = '📁' if file_info['is_directory'] else '📄'
        icon_label = Label(text=icon, size_hint_x=None, width='30dp')
        
        # Nome file/directory
        name_label = Label(
            text=file_info['name'], 
            text_size=(None, None),
            halign='left',
            valign='middle'
        )
        
        # Pulsanti azione
        actions_layout = BoxLayout(orientation='horizontal', size_hint_x=None, width='120dp')
        
        if file_info['is_directory']:
            open_btn = Button(text='Apri', size_hint_x=None, width='60dp')
            open_btn.bind(on_press=self.open_directory)
            actions_layout.add_widget(open_btn)
        else:
            download_btn = Button(text='↓', size_hint_x=None, width='60dp')
            download_btn.bind(on_press=self.download_file)
            actions_layout.add_widget(download_btn)
        
        delete_btn = Button(text='🗑', size_hint_x=None, width='60dp')
        delete_btn.bind(on_press=self.delete_item)
        actions_layout.add_widget(delete_btn)
        
        self.add_widget(icon_label)
        self.add_widget(name_label)
        self.add_widget(actions_layout)
    
    def open_directory(self, instance):
        """Apri directory"""
        self.app_instance.load_files(self.file_info['relative_path'])
    
    def download_file(self, instance):
        """Scarica file"""
        self.app_instance.download_file(self.file_info['relative_path'])
    
    def delete_item(self, instance):
        """Elimina file o directory"""
        self.app_instance.show_delete_confirmation(self.file_info)

class FileManagerApp(App):
    """App principale per la gestione file"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_url = "http://100.95.136.3:5000"  # Modifica con l'IP del tuo server
        self.current_path = ""
        
    def build(self):
        """Costruisci l'interfaccia"""
        main_layout = BoxLayout(orientation='vertical', padding='10dp', spacing='10dp')
        
        # Header con server URL e pulsanti
        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp')
        
        # Input server URL
        self.server_input = TextInput(
            text=self.server_url,
            hint_text='Server URL (es: http://100.95.136.3:5000)',
            multiline=False,
            size_hint_x=0.7
        )
        header_layout.add_widget(self.server_input)
        
        # Pulsante connetti
        connect_btn = Button(text='Connetti', size_hint_x=0.3)
        connect_btn.bind(on_press=self.connect_server)
        header_layout.add_widget(connect_btn)
        
        main_layout.add_widget(header_layout)
        
        # Barra di navigazione
        nav_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp')
        
        back_btn = Button(text='← Indietro', size_hint_x=0.3)
        back_btn.bind(on_press=self.go_back)
        nav_layout.add_widget(back_btn)
        
        self.path_label = Label(text='/', size_hint_x=0.7)
        nav_layout.add_widget(self.path_label)
        
        main_layout.add_widget(nav_layout)
        
        # Pulsanti azione
        action_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp')
        
        refresh_btn = Button(text='🔄 Aggiorna')
        refresh_btn.bind(on_press=self.refresh_files)
        action_layout.add_widget(refresh_btn)
        
        upload_btn = Button(text='📤 Carica')
        upload_btn.bind(on_press=self.show_upload_dialog)
        action_layout.add_widget(upload_btn)
        
        mkdir_btn = Button(text='📁+ Nuova Cartella')
        mkdir_btn.bind(on_press=self.show_mkdir_dialog)
        action_layout.add_widget(mkdir_btn)
        
        main_layout.add_widget(action_layout)
        
        # Lista file (scrollabile)
        self.files_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.files_layout.bind(minimum_height=self.files_layout.setter('height'))
        
        scroll = ScrollView()
        scroll.add_widget(self.files_layout)
        main_layout.add_widget(scroll)
        
        # Status bar
        self.status_label = Label(text='Pronto', size_hint_y=None, height='30dp')
        main_layout.add_widget(self.status_label)
        
        return main_layout
    
    def connect_server(self, instance):
        """Connetti al server"""
        self.server_url = self.server_input.text.strip()
        if not self.server_url.startswith('http'):
            self.server_url = 'http://' + self.server_url
        self.load_files()
    
    def load_files(self, path=""):
        """Carica la lista dei file dal server"""
        self.current_path = path
        self.path_label.text = f"/{path}" if path else "/"
        self.status_label.text = "Caricamento..."
        
        url = f"{self.server_url}/files"
        if path:
            url += f"/{path}"
        
        def on_success(request, result):
            self.status_label.text = f"Caricati {result.get('total', 0)} elementi"
            self.update_files_list(result.get('items', []))
        
        def on_error(request, error):
            self.status_label.text = f"Errore: {error}"
            self.show_popup("Errore", f"Impossibile caricare i file: {error}")
        
        UrlRequest(url, on_success=on_success, on_error=on_error)
    
    def update_files_list(self, files):
        """Aggiorna la lista dei file nell'interfaccia"""
        self.files_layout.clear_widgets()
        
        for file_info in files:
            file_item = FileItem(file_info, self)
            self.files_layout.add_widget(file_item)
    
    def go_back(self, instance):
        """Torna alla directory parent"""
        if self.current_path:
            parent_path = "/".join(self.current_path.split("/")[:-1])
            self.load_files(parent_path)
        else:
            self.load_files()
    
    def refresh_files(self, instance):
        """Ricarica i file"""
        self.load_files(self.current_path)
    
    def download_file(self, filepath):
        """Scarica un file"""
        self.status_label.text = f"Scaricando {filepath}..."
        
        url = f"{self.server_url}/download/{filepath}"
        
        def on_success(request, result):
            # Su Android, salva nella directory Downloads
            if platform == 'android':
                from android.storage import primary_external_storage_path
                downloads_path = os.path.join(primary_external_storage_path(), 'Download')
            else:
                downloads_path = os.path.expanduser('~/Downloads')
            
            filename = os.path.basename(filepath)
            save_path = os.path.join(downloads_path, filename)
            
            try:
                with open(save_path, 'wb') as f:
                    f.write(result)
                self.status_label.text = f"File salvato: {save_path}"
                self.show_popup("Successo", f"File scaricato in: {save_path}")
            except Exception as e:
                self.status_label.text = f"Errore salvataggio: {e}"
                self.show_popup("Errore", f"Errore nel salvare il file: {e}")
        
        def on_error(request, error):
            self.status_label.text = f"Errore download: {error}"
            self.show_popup("Errore", f"Errore nel download: {error}")
        
        UrlRequest(url, on_success=on_success, on_error=on_error)
    
    def show_upload_dialog(self, instance):
        """Mostra dialog per upload file"""
        content = BoxLayout(orientation='vertical', spacing='10dp')
        
        # File chooser
        filechooser = FileChooserListView()
        content.add_widget(filechooser)
        
        # Pulsanti
        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp')
        
        cancel_btn = Button(text='Annulla')
        upload_btn = Button(text='Carica')
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(upload_btn)
        content.add_widget(buttons_layout)
        
        popup = Popup(title='Seleziona file da caricare', content=content, size_hint=(0.9, 0.9))
        
        def upload_file(instance):
            if filechooser.selection:
                self.upload_file(filechooser.selection[0])
                popup.dismiss()
        
        def cancel(instance):
            popup.dismiss()
        
        upload_btn.bind(on_press=upload_file)
        cancel_btn.bind(on_press=cancel)
        
        popup.open()
    
    def upload_file(self, filepath):
        """Carica un file sul server"""
        self.status_label.text = f"Caricando {os.path.basename(filepath)}..."
        
        url = f"{self.server_url}/upload"
        
        def on_success(request, result):
            self.status_label.text = "File caricato con successo"
            self.refresh_files(None)
            self.show_popup("Successo", "File caricato con successo!")
        
        def on_error(request, error):
            self.status_label.text = f"Errore upload: {error}"
            self.show_popup("Errore", f"Errore nel caricamento: {error}")
        
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (os.path.basename(filepath), f.read())}
                data = {'path': self.current_path}
                
                UrlRequest(url, on_success=on_success, on_error=on_error, 
                          req_body=files, req_headers={'Content-Type': 'multipart/form-data'})
        except Exception as e:
            self.status_label.text = f"Errore lettura file: {e}"
            self.show_popup("Errore", f"Errore nella lettura del file: {e}")
    
    def show_mkdir_dialog(self, instance):
        """Mostra dialog per creare directory"""
        content = BoxLayout(orientation='vertical', spacing='10dp', padding='20dp')
        
        content.add_widget(Label(text='Nome della nuova cartella:'))
        
        name_input = TextInput(multiline=False, size_hint_y=None, height='40dp')
        content.add_widget(name_input)
        
        buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp')
        
        cancel_btn = Button(text='Annulla')
        create_btn = Button(text='Crea')
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(create_btn)
        content.add_widget(buttons_layout)
        
        popup = Popup(title='Nuova Cartella', content=content, size_hint=(0.8, 0.5))
        
        def create_directory(instance):
            if name_input.text.strip():
                self.create_directory(name_input.text.strip())
                popup.dismiss()
        
        def cancel(instance):
            popup.dismiss()
        
        create_btn.bind(on_press=create_directory)
        cancel_btn.bind(on_press=cancel)
        
        popup.open()
    
    def create_directory(self, name):
        """Crea una nuova directory"""
        self.status_label.text = f"Creando cartella {name}..."
        
        url = f"{self.server_url}/mkdir"
        data = json.dumps({'name': name, 'path': self.current_path})
        headers = {'Content-Type': 'application/json'}
        
        def on_success(request, result):
            self.status_label.text = "Cartella creata con successo"
            self.refresh_files(None)
            self.show_popup("Successo", "Cartella creata con successo!")
        
        def on_error(request, error):
            self.status_label.text = f"Errore creazione: {error}"
            self.show_popup("Errore", f"Errore nella creazione: {error}")
        
        UrlRequest(url, req_body=data, req_headers=headers, 
                  on_success=on_success, on_error=on_error)
    
    def show_delete_confirmation(self, file_info):
        """Mostra conferma eliminazione"""
        content = BoxLayout(orientation='vertical', spacing='20dp', padding='20dp')
        
        msg = f"Sei sicuro di voler eliminare:\n{file_info['name']}?"
        content.add_widget(Label(text=msg))
        
        buttons_layout = BoxLayout(orientation='horizontal')
        
        cancel_btn = Button(text='Annulla')
        delete_btn = Button(text='Elimina')
        
        buttons_layout.add_widget(cancel_btn)
        buttons_layout.add_widget(delete_btn)
        content.add_widget(buttons_layout)
        
        popup = Popup(title='Conferma Eliminazione', content=content, size_hint=(0.8, 0.5))
        
        def delete_item(instance):
            self.delete_item(file_info['relative_path'])
            popup.dismiss()
        
        def cancel(instance):
            popup.dismiss()
        
        delete_btn.bind(on_press=delete_item)
        cancel_btn.bind(on_press=cancel)
        
        popup.open()
    
    def delete_item(self, path):
        """Elimina un file o directory"""
        self.status_label.text = f"Eliminando {path}..."
        
        url = f"{self.server_url}/delete/{path}"
        
        def on_success(request, result):
            self.status_label.text = "Eliminato con successo"
            self.refresh_files(None)
            self.show_popup("Successo", "Elemento eliminato con successo!")
        
        def on_error(request, error):
            self.status_label.text = f"Errore eliminazione: {error}"
            self.show_popup("Errore", f"Errore nell'eliminazione: {error}")
        
        UrlRequest(url, method='DELETE', on_success=on_success, on_error=on_error)
    
    def show_popup(self, title, message):
        """Mostra popup informativo"""
        content = BoxLayout(orientation='vertical', spacing='20dp', padding='20dp')
        content.add_widget(Label(text=message))
        
        ok_btn = Button(text='OK', size_hint_y=None, height='50dp')
        content.add_widget(ok_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        ok_btn.bind(on_press=popup.dismiss)
        popup.open()

if __name__ == '__main__':
    FileManagerApp().run()