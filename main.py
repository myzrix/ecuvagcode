import logging
import sys

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

# Exemple de fonctionnalité : afficher une image avec matplotlib
if len(sys.argv) > 1:
    image_path = sys.argv[1]
    logging.info(f"Chargement de l'image depuis {image_path}")
    try:
        img = plt.imread(image_path)
        plt.figure()
        plt.imshow(img)
        plt.title("Image chargée")
        plt.axis('off')  # Désactiver les axes
        plt.show()
        logging.debug("Image affichée avec succès")
    except Exception as e:
        logging.error(f"Erreur lors du chargement ou de l'affichage de l'image: {e}")
else:
    logging.warning("Aucun chemin d'image fourni. Veuillez exécuter le script avec un chemin d'image en argument.")

logging.debug("Fin des fonctionnalités principales")

# Fermez les figures matplotlib
plt.close('all')
logging.info("Le script s'est terminé correctement.")
