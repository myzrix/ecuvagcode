#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logiciel de tuning d'ECU automobile pour ME7.5 et MED9
Interface graphique complète avec gestion de projets et comparaison de fichiers
"""

import sys
import os
import struct
from typing import Dict, List, Tuple, Optional, Union
import argparse
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Menu
import threading
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ECUTuner:
    """Classe principale pour le tuning d'ECU"""
    
    def __init__(self):
        self.supported_ecus = ['ME7.5', 'MED9']
        self.current_ecu = None
        self.data = bytearray()
        self.ecu_info = {}
        
    def load_ecu_file(self, filename: str) -> bool:
        """Charge un fichier ECU"""
        try:
            with open(filename, 'rb') as f:
                self.data = bytearray(f.read())
            return True
        except Exception as e:
            return False
    
    def detect_ecu_type(self, data: bytes) -> Optional[str]:
        """Détecte le type d'ECU à partir des données"""
        # Implémentation simplifiée - dans une vraie application,
        # cela nécessiterait une analyse plus complexe des signatures
        if len(data) > 1000000:  # Taille indicative
            # Vérification de signatures spécifiques
            if b'ME7.5' in data or b'ME75' in data:
                return 'ME7.5'
            elif b'MED9' in data:
                return 'MED9'
        return None
    
    def get_ecu_info(self) -> Dict:
        """Récupère les informations sur l'ECU"""
        if not self.data:
            return {}
            
        info = {
            'type': self.current_ecu,
            'size': len(self.data),
            'checksum': hashlib.md5(self.data).hexdigest(),
            'crc32': self.calculate_crc32(self.data)
        }
        return info
    
    def calculate_crc32(self, data: bytes) -> int:
        """Calcule le CRC32 d'un tableau d'octets"""
        crc = 0xFFFFFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xEDB88320
                else:
                    crc >>= 1
        return crc ^ 0xFFFFFFFF
    
    def get_ecu_parameters(self) -> Dict:
        """Récupère les paramètres disponibles pour l'ECU"""
        if not self.current_ecu:
            return {}
            
        parameters = {
            'ME7.5': {
                'lambda_target': {'offset': 0x1000, 'size': 4, 'unit': 'lambda'},
                'fuel_trim': {'offset': 0x1010, 'size': 4, 'unit': 'percent'},
                'ignition_timing': {'offset': 0x1020, 'size': 4, 'unit': 'degrees'},
                'boost_control': {'offset': 0x1030, 'size': 4, 'unit': 'bar'},
                'idle_control': {'offset': 0x1040, 'size': 4, 'unit': 'rpm'}
            },
            'MED9': {
                'lambda_target': {'offset': 0x2000, 'size': 4, 'unit': 'lambda'},
                'fuel_injection': {'offset': 0x2010, 'size': 4, 'unit': 'ms'},
                'ignition_timing': {'offset': 0x2020, 'size': 4, 'unit': 'degrees'},
                'turbo_control': {'offset': 0x2030, 'size': 4, 'unit': 'rpm'},
                'air_fuel_ratio': {'offset': 0x2040, 'size': 4, 'unit': 'ratio'}
            }
        }
        
        return parameters.get(self.current_ecu, {})
    
    def modify_parameter(self, param_name: str, new_value: Union[float, int]) -> bool:
        """Modifie un paramètre spécifique"""
        if not self.current_ecu:
            return False
            
        parameters = self.get_ecu_parameters()
        if param_name not in parameters:
            return False
            
        param_info = parameters[param_name]
        offset = param_info['offset']
        size = param_info['size']
        
        # Vérification de la taille du fichier
        if offset + size > len(self.data):
            return False
            
        # Conversion de la valeur en bytes
        try:
            if size == 1:
                self.data[offset] = int(new_value) & 0xFF
            elif size == 2:
                self.data[offset:offset+2] = struct.pack('<H', int(new_value) & 0xFFFF)
            elif size == 4:
                self.data[offset:offset+4] = struct.pack('<I', int(new_value) & 0xFFFFFFFF)
            else:
                return False
                
            return True
        except Exception:
            return False
    
    def save_file(self, filename: str) -> bool:
        """Sauvegarde le fichier modifié"""
        try:
            with open(filename, 'wb') as f:
                f.write(self.data)
            return True
        except Exception:
            return False

class ProjectManager:
    """Gestionnaire de projets"""
    
    def __init__(self):
        self.project_files = []
        self.project_name = ""
        self.project_path = ""
        
    def create_project(self, name: str, path: str) -> bool:
        """Crée un nouveau projet"""
        self.project_name = name
        self.project_path = path
        self.project_files = []
        return True
    
    def add_file_to_project(self, file_path: str) -> bool:
        """Ajoute un fichier au projet"""
        if file_path not in self.project_files:
            self.project_files.append(file_path)
            return True
        return False
    
    def save_project(self) -> bool:
        """Sauvegarde le projet"""
        if not self.project_path or not self.project_name:
            return False
            
        project_data = {
            'name': self.project_name,
            'files': self.project_files
        }
        
        try:
            with open(os.path.join(self.project_path, f"{self.project_name}.proj"), 'w') as f:
                json.dump(project_data, f)
            return True
        except Exception:
            return False
    
    def load_project(self, file_path: str) -> bool:
        """Charge un projet"""
        try:
            with open(file_path, 'r') as f:
                project_data = json.load(f)
            
            self.project_name = project_data.get('name', '')
            self.project_files = project_data.get('files', [])
            self.project_path = os.path.dirname(file_path)
            return True
        except Exception:
            return False

class ECUTunerGUI:
    """Interface graphique pour le tuner ECU"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ECU Tuner ME7.5 et MED9")
        self.root.geometry("1000x700")
        
        # Création du tuner
        self.tuner = ECUTuner()
        self.project_manager = ProjectManager()
        
        # Variables de l'interface
        self.file_path = tk.StringVar()
        self.ecu_type = tk.StringVar(value="Auto")  # Changement ici pour la détection automatique
        self.selected_param = tk.StringVar()
        self.param_value = tk.StringVar()
        self.current_view = tk.StringVar(value="1D")
        
        self.setup_menu()
        self.setup_ui()
        
    def setup_menu(self):
        """Configure le menu principal"""
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Fichier
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau Projet", command=self.new_project)
        file_menu.add_command(label="Ouvrir Projet", command=self.open_project)
        file_menu.add_command(label="Enregistrer Projet", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="Charger Fichier", command=self.load_file)
        file_menu.add_command(label="Sauvegarder Fichier", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.root.quit)
        
        # Menu Affichage
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_radiobutton(label="Vue 1D", variable=self.current_view, value="1D", command=self.update_view)
        view_menu.add_radiobutton(label="Vue 2D", variable=self.current_view, value="2D", command=self.update_view)
        view_menu.add_radiobutton(label="Vue 3D", variable=self.current_view, value="3D", command=self.update_view)
        
        # Menu Outils
        tools_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="Comparateur de fichiers", command=self.open_comparator)
        tools_menu.add_command(label="Afficher Structure", command=self.show_structure)
        
        # Menu Aide
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self.show_about)
        
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuration du grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Section chargement de fichier
        file_frame = ttk.LabelFrame(main_frame, text="Fichier ECU", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Fichier:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.file_path, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(file_frame, text="Parcourir", command=self.browse_file).grid(row=0, column=2)
        
        # Type d'ECU
        ttk.Label(file_frame, text="Type d'ECU:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0), padx=(0, 5))
        ecu_combo = ttk.Combobox(file_frame, textvariable=self.ecu_type, values=['ME7.5', 'MED9'], state="readonly")
        ecu_combo.grid(row=1, column=1, sticky=tk.W, pady=(5, 0), padx=(0, 5))
        
        # Boutons
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Charger", command=self.load_file).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Détecter", command=self.detect_ecu).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Sauvegarder", command=self.save_file).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="Ajouter au Projet", command=self.add_to_project).grid(row=0, column=3, padx=(0, 5))
        
        # Section paramètres
        param_frame = ttk.LabelFrame(main_frame, text="Paramètres", padding="10")
        param_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        param_frame.columnconfigure(1, weight=1)
        param_frame.rowconfigure(1, weight=1)
        
        # Liste des paramètres
        ttk.Label(param_frame, text="Paramètres disponibles:").grid(row=0, column=0, sticky=tk.W)
        
        self.param_listbox = tk.Listbox(param_frame, height=8)
        self.param_listbox.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        self.param_listbox.bind('<<ListboxSelect>>', self.on_param_select)
        
        # Valeur du paramètre
        ttk.Label(param_frame, text="Nouvelle valeur:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        ttk.Entry(param_frame, textvariable=self.param_value, width=20).grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(param_frame, text="Modifier", command=self.modify_param).grid(row=3, column=1, sticky=tk.W, pady=(5, 0), padx=(5, 0))
        
        # Informations ECU
        info_frame = ttk.LabelFrame(main_frame, text="Informations ECU", padding="10")
        info_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        info_frame.columnconfigure(0, weight=1)
        
        self.info_text = tk.Text(info_frame, height=5, wrap=tk.WORD)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Barre de progression
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Zone d'affichage selon la vue
        self.view_frame = ttk.LabelFrame(main_frame, text="Affichage", padding="10")
        self.view_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.view_frame.columnconfigure(0, weight=1)
        self.view_frame.rowconfigure(0, weight=1)
        
        self.view_display = FigureCanvasTkAgg(plt.figure(figsize=(8, 4)), master=self.view_frame)
        self.view_display.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def update_view(self):
        """Met à jour l'affichage selon la vue sélectionnée"""
        view_type = self.current_view.get()
        if not self.tuner.data:
            return
        
        plt.figure(figsize=(8, 4))
        plt.clf()
        
        if view_type == "1D":
            plt.plot(range(len(self.tuner.data)), self.tuner.data)
            plt.title("Vue 1D")
            plt.xlabel("Octet")
            plt.ylabel("Valeur")
        elif view_type == "2D":
            data_2d = [self.tuner.data[i:i+100] for i in range(0, len(self.tuner.data), 100)]
            plt.imshow(data_2d, aspect='auto', cmap='gray')
            plt.title("Vue 2D")
            plt.xlabel("Octet")
            plt.ylabel("Bloc")
        elif view_type == "3D":
            data_3d = [self.tuner.data[i:i+100] for i in range(0, len(self.tuner.data), 100)]
            ax = plt.figure().add_subplot(projection='3d')
            x = list(range(len(data_3d)))
            y = list(range(len(data_3d[0])))
            X, Y = np.meshgrid(x, y)
            Z = np.array(data_3d).T
            ax.plot_surface(X, Y, Z, cmap='viridis')
            plt.title("Vue 3D")
        
        self.view_display.draw()
    
    def browse_file(self):
        """Ouvre une boîte de dialogue pour choisir un fichier"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier ECU",
            initialdir=os.path.expanduser("~"),
            filetypes=[("Fichiers ECU", "*.bin"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            self.file_path.set(file_path)
    
    def load_file(self):
        """Charge le fichier ECU"""
        if not self.file_path.get():
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un fichier")
            return
            
        self.progress.start()
        self.root.update()
        
        try:
            if self.tuner.load_ecu_file(self.file_path.get()):
                self.update_info()
                messagebox.showinfo("Succès", "Fichier chargé avec succès")
            else:
                messagebox.showerror("Erreur", "Impossible de charger le fichier")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement: {str(e)}")
        finally:
            self.progress.stop()
    
    def detect_ecu(self):
        """Détecte automatiquement le type d'ECU"""
        if not self.file_path.get():
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un fichier")
            return
            
        self.progress.start()
        self.root.update()
        
        try:
            detected_type = self.tuner.detect_ecu_type(self.tuner.data)
            if detected_type:
                self.ecu_type.set(detected_type)
                self.tuner.current_ecu = detected_type
                self.update_info()
                messagebox.showinfo("Succès", f"ECU détecté: {detected_type}")
            else:
                messagebox.showwarning("Avertissement", "Impossible de détecter le type d'ECU")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la détection: {str(e)}")
        finally:
            self.progress.stop()
    
    def save_file(self):
        """Sauvegarde le fichier modifié"""
        if not self.file_path.get():
            messagebox.showwarning("Avertissement", "Aucun fichier chargé")
            return
            
        save_path = filedialog.asksaveasfilename(
            title="Sauvegarder le fichier modifié",
            initialdir=os.path.expanduser("~"),
            defaultextension=".bin",
            filetypes=[("Fichiers ECU", "*.bin"), ("Tous les fichiers", "*.*")]
        )
        
        if save_path:
            self.progress.start()
            self.root.update()
            
            try:
                if self.tuner.save_file(save_path):
                    messagebox.showinfo("Succès", "Fichier sauvegardé avec succès")
                else:
                    messagebox.showerror("Erreur", "Impossible de sauvegarder le fichier")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")
            finally:
                self.progress.stop()
    
    def show_structure(self):
        """Affiche la structure de l'ECU"""
        if not self.tuner.current_ecu:
            messagebox.showwarning("Avertissement", "Aucun ECU détecté")
            return
            
        self.progress.start()
        self.root.update()
        
        try:
            parameters = self.tuner.get_ecu_parameters()
            info = f"=== Structure de l'ECU {self.tuner.current_ecu} ===\n"
            info += f"Taille du fichier: {len(self.tuner.data)} octets\n"
            info += f"Checksum MD5: {self.tuner.ecu_info.get('checksum', 'N/A')}\n"
            info += f"CRC32: {self.tuner.ecu_info.get('crc32', 'N/A')}\n\n"
            info += "Paramètres disponibles:\n"
            
            for name, info_dict in parameters.items():
                info += f"  {name}: offset 0x{info_dict['offset']:04X}, taille {info_dict['size']} octets, unité {info_dict['unit']}\n"
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'affichage: {str(e)}")
        finally:
            self.progress.stop()
    
    def update_info(self):
        """Met à jour les informations de l'ECU"""
        if not self.tuner.data:
            return
            
        self.tuner.ecu_info = self.tuner.get_ecu_info()
        
        info = f"Type: {self.tuner.current_ecu or 'Non détecté'}\n"
        info += f"Taille: {len(self.tuner.data)} octets\n"
        info += f"Checksum MD5: {self.tuner.ecu_info.get('checksum', 'N/A')}\n"
        info += f"CRC32: {self.tuner.ecu_info.get('crc32', 'N/A')}\n"
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
        
        # Mettre à jour la liste des paramètres
        self.update_param_list()
    
    def update_param_list(self):
        """Met à jour la liste des paramètres"""
        self.param_listbox.delete(0, tk.END)
        
        if self.tuner.current_ecu:
            parameters = self.tuner.get_ecu_parameters()
            for name in parameters.keys():
                self.param_listbox.insert(tk.END, name)
    
    def on_param_select(self, event):
        """Gère la sélection d'un paramètre"""
        selection = self.param_listbox.curselection()
        if selection:
            self.selected_param.set(self.param_listbox.get(selection[0]))
    
    def modify_param(self):
        """Modifie un paramètre"""
        if not self.selected_param.get():
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un paramètre")
            return
            
        if not self.param_value.get():
            messagebox.showwarning("Avertissement", "Veuillez entrer une valeur")
            return
            
        try:
            value = float(self.param_value.get())
            
            self.progress.start()
            self.root.update()
            
            if self.tuner.modify_parameter(self.selected_param.get(), value):
                messagebox.showinfo("Succès", f"Paramètre {self.selected_param.get()} modifié avec succès")
                self.update_info()
            else:
                messagebox.showerror("Erreur", "Impossible de modifier le paramètre")
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer une valeur numérique valide")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la modification: {str(e)}")
        finally:
            self.progress.stop()
    
    def new_project(self):
        """Crée un nouveau projet"""
        project_name = tk.simpledialog.askstring("Nouveau Projet", "Nom du projet:")
        if project_name:
            project_path = filedialog.askdirectory(title="Sélectionner le dossier du projet")
            if project_path:
                if self.project_manager.create_project(project_name, project_path):
                    messagebox.showinfo("Succès", f"Projet {project_name} créé avec succès")
                else:
                    messagebox.showerror("Erreur", "Impossible de créer le projet")
    
    def open_project(self):
        """Ouvre un projet existant"""
        file_path = filedialog.askopenfilename(
            title="Ouvrir un projet",
            filetypes=[("Fichiers projet", "*.proj"), ("Tous les fichiers", "*.*")]
        )
        if file_path:
            if self.project_manager.load_project(file_path):
                messagebox.showinfo("Succès", "Projet chargé avec succès")
            else:
                messagebox.showerror("Erreur", "Impossible de charger le projet")
    
    def save_project(self):
        """Sauvegarde le projet en cours"""
        if self.project_manager.project_name:
            if self.project_manager.save_project():
                messagebox.showinfo("Succès", "Projet sauvegardé avec succès")
            else:
                messagebox.showerror("Erreur", "Impossible de sauvegarder le projet")
        else:
            messagebox.showwarning("Avertissement", "Aucun projet en cours")
    
    def add_to_project(self):
        """Ajoute le fichier actuel au projet"""
        if not self.file_path.get():
            messagebox.showwarning("Avertissement", "Veuillez charger un fichier")
            return
            
        if self.project_manager.add_file_to_project(self.file_path.get()):
            messagebox.showinfo("Succès", "Fichier ajouté au projet")
        else:
            messagebox.showwarning("Avertissement", "Fichier déjà dans le projet")
    
    def open_comparator(self):
        """Ouvre le comparateur de fichiers"""
        # Création d'une nouvelle fenêtre pour le comparateur
        comp_window = tk.Toplevel(self.root)
        comp_window.title("Comparateur de fichiers")
        comp_window.geometry("600x400")
        
        # Zone de sélection des fichiers
        ttk.Label(comp_window, text="Fichier 1:").grid(row=0, column=0, sticky=tk.W, padx=(10, 5), pady=(10, 5))
        file1_var = tk.StringVar()
        ttk.Entry(comp_window, textvariable=file1_var, width=40).grid(row=0, column=1, padx=(0, 5), pady=(10, 5))
        ttk.Button(comp_window, text="Parcourir", command=lambda: self.select_file(file1_var, comp_window)).grid(row=0, column=2, padx=(0, 10), pady=(10, 5))
        
        ttk.Label(comp_window, text="Fichier 2:").grid(row=1, column=0, sticky=tk.W, padx=(10, 5), pady=(5, 10))
        file2_var = tk.StringVar()
        ttk.Entry(comp_window, textvariable=file2_var, width=40).grid(row=1, column=1, padx=(0, 5), pady=(5, 10))
        ttk.Button(comp_window, text="Parcourir", command=lambda: self.select_file(file2_var, comp_window)).grid(row=1, column=2, padx=(0, 10), pady=(5, 10))
        
        # Bouton de comparaison
        ttk.Button(comp_window, text="Comparer", command=lambda: self.compare_files(
            file1_var.get(), file2_var.get(), comp_window)).grid(row=2, column=1, pady=(10, 10))
        
        # Zone de résultats
        result_text = tk.Text(comp_window, height=15, width=70)
        result_text.grid(row=3, column=0, columnspan=3, padx=10, pady=(10, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        result_text.config(state=tk.DISABLED)
    
    def select_file(self, file_var, window):
        """Sélectionne un fichier parmi les fichiers du projet"""
        if self.project_manager.project_files:
            file_path = filedialog.askopenfilename(
                title="Sélectionner un fichier",
                initialdir=self.project_manager.project_path,
                filetypes=[("Fichiers ECU", "*.bin"), ("Tous les fichiers", "*.*")]
            )
            if file_path:
                file_var.set(file_path)
        else:
            messagebox.showwarning("Avertissement", "Aucun fichier dans le projet")
    
    def compare_files(self, file1_path, file2_path, window):
        """Compare deux fichiers"""
        try:
            with open(file1_path, 'rb') as f1, open(file2_path, 'rb') as f2:
                data1 = f1.read()
                data2 = f2.read()
            
            # Comparaison des tailles
            if len(data1) != len(data2):
                result = f"Tailles différentes : {len(data1)} vs {len(data2)} octets\n"
            else:
                result = f"Tailles identiques : {len(data1)} octets\n"
            
            # Comparaison des checksums
            md5_1 = hashlib.md5(data1).hexdigest()
            md5_2 = hashlib.md5(data2).hexdigest()
            result += f"MD5 1: {md5_1}\n"
            result += f"MD5 2: {md5_2}\n"
            
            if md5_1 == md5_2:
                result += "Les fichiers sont identiques\n"
            else:
                result += "Les fichiers sont différents\n"
            
            # Affichage des différences
            result += "\nDifférences :\n"
            differences = 0
            for i, (b1, b2) in enumerate(zip(data1, data2)):
                if b1 != b2:
                    result += f"Octet {i:06X} : {b1:02X} vs {b2:02X}\n"
                    differences += 1
                    if differences > 20:  # Limite pour éviter le trop de résultats
                        result += f"... et {len(data1) - i} différences supplémentaires\n"
                        break
            
            if differences == 0 and len(data1) == len(data2):
                result += "Aucune différence trouvée\n"
            
            # Affichage dans la fenêtre
            result_text = window.nametowidget(window.winfo_children()[6])  # Récupère le Text widget
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(1.0, result)
            result_text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la comparaison : {str(e)}")
    
    def show_about(self):
        """Affiche les informations à propos"""
        messagebox.showinfo("À propos", "ECU Tuner ME7.5 et MED9\nVersion 1.0\nLogiciel de tuning d'ECU automobile")

def main():
    """Fonction principale"""
    # Création de la fenêtre principale
    root = tk.Tk()
    
    # Configuration de l'apparence
    style = ttk.Style()
    try:
        style.theme_use('clam')  # Thème moderne si disponible
    except:
        pass  # Utiliser le thème par défaut si 'clam' n'est pas disponible
    
    # Création de l'interface
    app = ECUTunerGUI(root)
    
    # Lancement de l'interface
    root.mainloop()

if __name__ == "__main__":
    main()
