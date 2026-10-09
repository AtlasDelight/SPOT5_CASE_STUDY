# main.py
from spot_solver import resoudre_planification

def main():
    fichiers_donnees = ["spotProba1", "spotProba2", "spotProba3", "spotProba4", "spotProba5"]
    modes = ["optimiste", "pessimiste"]

    for fichier in fichiers_donnees:
        for mode in modes:
            print("=" * 70)
            print(f"RESOLUTION DU JEU DE DONNEES : {fichier} | MODE : {mode.upper()}")
            print("=" * 70 + "\n")
            
            try:
                resoudre_planification(fichier, mode)
            except Exception as e:
                print(f"Erreur lors de l'exécution de {fichier} : {e}\n")

if __name__ == "__main__":
    main()