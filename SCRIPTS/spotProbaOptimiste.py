# Resolution d'un problème de planification de prise de vue sous incertitude
#
# Fichier complété à partir de spotProbaPartial.py

from pyscipopt import Model, quicksum
from itertools import product

# On charge les données (remplacez spotProba5 par le fichier de test souhaité)
from spotProba5 import nbImages, nbInstruments, PA, DD, AN, VI, DU, TY, PM, PMmax, Failure, ProbaInf, ProbaSup

# Creation du modele lineaire
mymodel = Model("Optimiste")

# Variables de decision
selection = {}
for i in range(nbImages):
    selection[i] = mymodel.addVar(vtype='B', name='select' + str(i))

assignedTo = {}
for i in range(nbImages):
    ass_i = {}
    for j in range(nbInstruments):
        ass_i[j] = mymodel.addVar(vtype='B', name='assignto' + str(i) + '_' + str(j))
    assignedTo[i] = ass_i

# --- NOUVELLES CONTRAINTES ---

# 1. Contrainte de mémoire : La somme de la mémoire des images retenues ne dépasse pas PMmax
mymodel.addCons(quicksum(PM[i] * selection[i] for i in range(nbImages)) <= PMmax, "Memoire")

# 2. Contraintes de typologie d'images (Mono vs Stéréo)
for i in range(nbImages):
    if TY[i] == 1:
        # Mono : affectée à exactement un instrument si sélectionnée
        mymodel.addCons(quicksum(assignedTo[i][j] for j in range(nbInstruments)) == selection[i], "Mono_" + str(i))
    elif TY[i] == 2:
        # Stéréo : affectée obligatoirement à l'avant (0) et l'arrière (2), jamais au nadir (1)
        mymodel.addCons(assignedTo[i][0] == selection[i], "Stereo_0_" + str(i))
        mymodel.addCons(assignedTo[i][2] == selection[i], "Stereo_2_" + str(i))
        mymodel.addCons(assignedTo[i][1] == 0, "Stereo_1_" + str(i))

# 3. Contrainte de non chevauchement (issue du code d'origine)
for ima1, ima2 in product(range(nbImages), range(nbImages)):
    if ima1 < ima2:
        for ins in range(nbInstruments):
            if abs(DD[ima1][ins] - DD[ima2][ins]) * VI < DU * VI + abs(AN[ima1][ins] - AN[ima2][ins]):
                mymodel.addCons(assignedTo[ima1][ins] + assignedTo[ima2][ins] <= 1, "Chevauchement_" + str(ima1) + "_" + str(ima2))

# --- FONCTION OBJECTIF SOUS INCERTITUDE ---

obj_terms = []
for i in range(nbImages):
    # Risque météo : On utilise ProbaInf (Optimiste)
    proba_succes_meteo = 1.0 - ProbaInf[i]
    
    if TY[i] == 1:
        # Gain attendu pour une image mono sur l'instrument j
        for j in range(nbInstruments):
            gain = PA[i] * proba_succes_meteo * (1.0 - Failure[j])
            obj_terms.append(gain * assignedTo[i][j])
    elif TY[i] == 2:
        # Gain attendu pour une image stéréo (doit utiliser 0 et 2, succès si aucun des deux ne tombe en panne)
        gain = PA[i] * proba_succes_meteo * (1.0 - Failure[0]) * (1.0 - Failure[2])
        obj_terms.append(gain * selection[i])

mymodel.setObjective(quicksum(obj_terms), sense='maximize')

# --- RESOLUTION ---

mymodel.writeProblem("pb_Optimiste.cip")

print("Resolution Optimiste")
mymodel.hideOutput(False)
mymodel.optimize()

print('statut ' + mymodel.getStatus())

if mymodel.getStatus() == 'optimal':
    print("\n\nProblème resolu, valeur de l'objectif " + str(mymodel.getObjVal()))
    for ima in range(nbImages):
        for ins in range(nbInstruments):
            if (mymodel.getVal(assignedTo[ima][ins]) > 0.5):
                print("Image" + str(ima) + " (Type " + str(TY[ima]) + ") selectionnée et assignée à " + str(ins) + " (debut à " + str(DD[ima][ins]) + ")")
