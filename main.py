import logging

# Configurez le logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    logging.error("Le module matplotlib n'est pas installé. Veuillez exécuter 'pip install -r requirements.txt' pour l'installer.")
    exit(1)

logging.info("Le script a démarré correctement.")

# Le reste de votre code ici
