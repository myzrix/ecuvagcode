import logging

# Configurez le logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    logging.error("Le module matplotlib n'est pas installé. Veuillez exécuter 'pip install -r requirements.txt' pour l'installer.")
    exit(1)

logging.info("Le script a démarré correctement.")

# Ajoutez vos fonctionnalités ici
logging.debug("Début des fonctionnalités principales")

# Exemple de fonctionnalité : afficher une figure matplotlib
try:
    logging.debug("Création d'une figure")
    plt.figure()
    logging.debug("Figure créée avec succès")
except Exception as e:
    logging.error(f"Erreur lors de la création de la figure: {e}")

logging.debug("Fin des fonctionnalités principales")

# Fermez les figures matplotlib
plt.close('all')
logging.info("Le script s'est terminé correctement.")
