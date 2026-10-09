# spot_solver.py
# Fichier complété à partir de spotProbaPartial.py

import importlib
from pyscipopt import Model, quicksum
from itertools import product

def resoudre_planification(nom_fichier, mode="pessimiste"):
    """
    Fonction qui charge un jeu de données et résout le problème
    selon le mode choisi ('optimiste' ou 'pessimiste').
    """
    # 1. Chargement dynamique des données
    data = importlib.import_module(nom_fichier)
    
    nbImages = data.nbImages
    nbInstruments = data.nbInstruments
    PA = data.PA
    DD = data.DD
    AN = data.AN
    VI = data.VI
    DU = data.DU
    TY = data.TY
    PM = data.PM
    PMmax = data.PMmax
    Failure = data.Failure
    ProbaInf = data.ProbaInf
    ProbaSup = data.ProbaSup

    # 2. Création du modèle linéaire
    mymodel = Model(f"SPOT_{nom_fichier}_{mode}")
    
    # On laisse SCIP afficher ses logs bruts
    mymodel.hideOutput(False)

    # Variables de décision
    selection = {}
    for i in range(nbImages):
        selection[i] = mymodel.addVar(vtype='B', name='select_' + str(i))

    assignedTo = {}
    for i in range(nbImages):
        ass_i = {}
        for j in range(nbInstruments):
            ass_i[j] = mymodel.addVar(vtype='B', name='assignto_' + str(i) + '_' + str(j))
        assignedTo[i] = ass_i

    # 3. La fonction objectif
    obj_terms = []
    for i in range(nbImages):
        if mode == "optimiste":
            proba_meteo = 1.0 - ProbaInf[i]
        else: # mode == "pessimiste"
            proba_meteo = 1.0 - ProbaSup[i]

        if TY[i] == 1:
            for j in range(nbInstruments):
                gain = PA[i] * proba_meteo * (1.0 - Failure[j])
                obj_terms.append(gain * assignedTo[i][j])
        elif TY[i] == 2:
            gain = PA[i] * proba_meteo * (1.0 - Failure[0]) * (1.0 - Failure[2])
            obj_terms.append(gain * selection[i])

    mymodel.setObjective(quicksum(obj_terms), sense='maximize')

    # 4. Ajout des contraintes
    # Contrainte de mémoire
    mymodel.addCons(quicksum(PM[i] * selection[i] for i in range(nbImages)) <= PMmax, name="capacite_memoire")

    # Contraintes de liaison selon le type d'image (Mono/Stéréo)
    for i in range(nbImages):
        if TY[i] == 1:
            mymodel.addCons(quicksum(assignedTo[i][j] for j in range(nbInstruments)) == selection[i])
        elif TY[i] == 2:
            mymodel.addCons(assignedTo[i][0] == selection[i])
            mymodel.addCons(assignedTo[i][2] == selection[i])
            mymodel.addCons(assignedTo[i][1] == 0)

    # Contrainte de non-chevauchement
    for ima1, ima2 in product(range(nbImages), range(nbImages)):
        if ima1 < ima2:
            for ins in range(nbInstruments):
                if abs(DD[ima1][ins] - DD[ima2][ins]) * VI < DU * VI + abs(AN[ima1][ins] - AN[ima2][ins]):
                    mymodel.addCons(assignedTo[ima1][ins] + assignedTo[ima2][ins] <= 1)

    # 5. Résolution
    mymodel.optimize()
    
    # On ajoute un petit récapitulatif à la fin des logs de SCIP
    print("\n--- SYNTHESE DES RESULTATS ---")
    print(f"Statut final : {mymodel.getStatus()}")
    if mymodel.getStatus() == 'optimal':
        print("\n\nProblème resolu, valeur de l'objectif " + str(mymodel.getObjVal()))
        for ima in range(nbImages):
            for ins in range(nbInstruments):
                if (mymodel.getVal(assignedTo[ima][ins]) > 0.5):
                    print("Image" + str(ima) + " (Type " + str(TY[ima]) + ") selectionnée et assignée à " + str(ins) + " (debut à " + str(DD[ima][ins]) + ")")

    print("-" * 50 + "\n\n")