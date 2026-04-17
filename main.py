#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logiciel de tuning d'ECU automobile pour ME7.5 et MED9
"""

import sys
import os
import struct
from typing import Dict, List, Tuple, Optional, Union
import argparse
import hashlib

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
            print(f"Fichier {filename} chargé avec succès")
            return True
        except Exception as e:
            print(f"Erreur lors du chargement du fichier {filename}: {e}")
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
            print("Aucun ECU détecté")
            return False
            
        parameters = self.get_ecu_parameters()
        if param_name not in parameters:
            print(f"Paramètre {param_name} non trouvé")
            return False
            
        param_info = parameters[param_name]
        offset = param_info['offset']
        size = param_info['size']
        
        # Vérification de la taille du fichier
        if offset + size > len(self.data):
            print(f"Erreur: offset {offset} dépasse la taille du fichier")
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
                print(f"Taille de paramètre non supportée: {size}")
                return False
                
            print(f"Modification du paramètre {param_name} à {new_value}")
            return True
        except Exception as e:
            print(f"Erreur lors de la modification du paramètre {param_name}: {e}")
            return False
    
    def save_file(self, filename: str) -> bool:
        """Sauvegarde le fichier modifié"""
        try:
            with open(filename, 'wb') as f:
                f.write(self.data)
            print(f"Fichier sauvegardé sous {filename}")
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
            return False
    
    def dump_ecu_structure(self) -> None:
        """Affiche la structure de l'ECU"""
        print(f"\n=== Structure de l'ECU {self.current_ecu} ===")
        print(f"Taille du fichier: {len(self.data)} octets")
        print(f"Checksum MD5: {self.ecu_info.get('checksum', 'N/A')}")
        print(f"CRC32: {self.ecu_info.get('crc32', 'N/A')}")
        
        parameters = self.get_ecu_parameters()
        print("\nParamètres disponibles:")
        for name, info in parameters.items():
            print(f"  {name}: offset 0x{info['offset']:04X}, taille {info['size']} octets, unité {info['unit']}")

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Tuner d\'ECU automobile ME7.5 et MED9')
    parser.add_argument('input_file', help='Fichier ECU à tuner')
    parser.add_argument('--output', '-o', help='Fichier de sortie')
    parser.add_argument('--ecu-type', '-t', choices=['ME7.5', 'MED9'], 
                       help='Type d\'ECU (ME7.5 ou MED9)')
    parser.add_argument('--param', '-p', nargs=2, metavar=('PARAM', 'VALUE'),
                       help='Modifier un paramètre (nom valeur)')
    parser.add_argument('--list-params', action='store_true',
                       help='Lister les paramètres disponibles')
    parser.add_argument('--dump', action='store_true',
                       help='Afficher la structure de l\'ECU')
    
    args = parser.parse_args()
    
    # Création de l'instance du tuner
    tuner = ECUTuner()
    
    # Chargement du fichier
    if not tuner.load_ecu_file(args.input_file):
        sys.exit(1)
    
    # Détection du type d'ECU
    if args.ecu_type:
        tuner.current_ecu = args.ecu_type
    else:
        detected_type = tuner.detect_ecu_type(tuner.data)
        if detected_type:
            tuner.current_ecu = detected_type
            print(f"ECU détecté: {detected_type}")
        else:
            print("Impossible de détecter le type d'ECU")
            sys.exit(1)
    
    # Récupération des informations
    tuner.ecu_info = tuner.get_ecu_info()
    
    # Affichage de la structure si demandé
    if args.dump:
        tuner.dump_ecu_structure()
        sys.exit(0)
    
    # Liste des paramètres si demandé
    if args.list_params:
        parameters = tuner.get_ecu_parameters()
        print("Paramètres disponibles:")
        for name, info in parameters.items():
            print(f"  {name}: offset 0x{info['offset']:04X}, taille {info['size']} octets, unité {info['unit']}")
        sys.exit(0)
    
    # Modification de paramètre si spécifié
    if args.param:
        param_name, param_value = args.param
        try:
            value = float(param_value)
            tuner.modify_parameter(param_name, value)
        except ValueError:
            print("Erreur: la valeur doit être un nombre")
            sys.exit(1)
    
    # Sauvegarde
    if args.output:
        tuner.save_file(args.output)
    else:
        output_file = f"tuned_{os.path.basename(args.input_file)}"
        tuner.save_file(output_file)

if __name__ == "__main__":
    main()
