#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logiciel de tuning d'ECU automobile pour ME7.5 et MED9
Interface graphique compatible Windows et Linux
"""

import sys
import os
import struct
from typing import Dict, List, Tuple, Optional, Union
import argparse
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

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
            'crc32': hashlib.crc32(self.data) & 0xffffffff
        }
        return info
    
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

class ECUTunerGUI:
    """Interface graphique pour le tuner ECU"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ECU Tuner ME7.5 et MED9")
        self.root.geometry("800x600")
        
        # Création du tuner
        self.tuner = ECUTuner()
        
        # Variables de l'interface
        self.file_path = tk.StringVar()
        self.ecu_type = tk.StringVar()
        self.selected_param = tk.StringVar()
        self.param_value = tk.StringVar()
        
        self.setup_ui()
        
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
        ecu_combo.set("Auto")
        
        # Boutons
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        ttk.Button(button_frame, text="Charger", command=self.load_file).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Détecter", command=self.detect_ecu).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Sauvegarder", command=self.save_file).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(button_frame, text="Afficher Structure", command=self.show_structure).grid(row=0, column=3, padx=(0, 5))
        
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
        
    def browse_file(self):
        """Ouvre une boîte de dialogue pour choisir un fichier"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier ECU",
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
