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
import numpy as np  # Add this line

class ECUTuner:
    """Classe principale pour le tuning d'ECU"""
    
    def __init__(self):
        self.supported_ecus = ['ME7.5', 'MED9']
        self.current_ecu = None
        self.data = bytearray()
        self.ecu_info = {}
        
    # ... (rest of the code remains unchanged)
