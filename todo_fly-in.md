# ✅ TODO LIST — Fly-in

## Phase 1 — Setup du projet

- [*] **1. Créer l'arborescence**
  ```
  fly-in/
  ├── src/
  ├── maps/
  ├── tests/
  ├── README.md
  ├── Makefile
  ├── requirements.txt
  └── .gitignore
  ```

- [*] **2. Configurer l'environnement** — installer `flake8`, `mypy`, `pytest`

- [*] **3. Configurer le Makefile** — cibles : `install`, `run`, `debug`, `clean`, `lint` *(obligatoire)*

---

## Phase 2 — Modèles ⚠️ *Avant le parser*

- [*] **4. Classe `Hub`** — attributs : `name`, `x`, `y`, `zone_type`, `color`, `max_drones`, `neighbors`
- [*] **5. Classe `Connection`** — attributs : `source`, `target`, `capacity`
- [*] **6. Classe `Drone`** — attributs : `id`, `current_hub`, `path`, `state`, `remaining_turns`
- [*] **7. Classe `Graph`** — contient : `hubs`, `connections`, `start`, `end`, `nb_drones`

---

## Phase 3 — Parser

- [ ] **8. Lire le fichier ligne par ligne** — gérer lignes vides et commentaires `#`
- [ ] **9. Parser `nb_drones`** — vérifier : présent, entier positif
- [ ] **10. Parser `start_hub`** — vérifier : unique, nom valide, coordonnées valides
- [ ] **11. Parser `end_hub`** — même logique que `start_hub`
- [ ] **12. Parser les hubs** — `hub: roof1 3 4 [zone=restricted color=red]` → nom, x, y, metadata
- [ ] **13. Parser les metadata** — zones : `normal`, `restricted`, `priority`, `blocked` / champs : `zone`, `color`, `max_drones`
- [ ] **14. Parser les connexions** — `connection: A-B`
- [ ] **15. Parser les metadata de connexion** — `connection: A-B [max_link_capacity=2]`
- [ ] **16. Vérifications obligatoires** *(insisté dans le sujet)* :
  - [ ] Pas de doublon hub / connexion
  - [ ] Hubs référencés existants
  - [ ] Types valides
  - [ ] Capacités positives
  - [ ] `start` et `end` uniques
- [ ] **17. Gérer les erreurs proprement** — créer `exceptions.py` avec `class ParserError(Exception)`

---

## Phase 4 — Construction du graphe

- [ ] **18. Ajouter les voisins automatiquement** — connexion `A-B` → A connaît B et B connaît A
- [ ] **19. Tester le graphe** — afficher hubs, voisins, connexions via `print(graph)`

---

## Phase 5 — Pathfinding simple

- [ ] **20. BFS basique** — trouver un chemin simple `start → end`
- [ ] **21. Ignorer temporairement** — capacités, collisions, multi-drones
- [ ] **22. Tester avec une petite map** — créer `maps/test_simple.txt`

---

## Phase 6 — Simulation 1 drone

- [ ] **23. Créer `SimulationEngine`**
- [ ] **24. Faire avancer 1 drone** — tour par tour
- [ ] **25. Afficher les mouvements** *(format obligatoire)* :
  ```
  D1-A
  D1-B
  D1-end
  ```

---

## Phase 7 — Multi-drones

- [ ] **26. Ajouter plusieurs drones** — tous partent du `start`
- [ ] **27. Gérer l'occupation des hubs** — 1 drone max par défaut
- [ ] **28. Respecter `max_drones`** — `[max_drones=3]`
- [ ] **29. Respecter `max_link_capacity`** — `[max_link_capacity=2]`

---

## Phase 8 — Zones restricted ⚠️ *Important*

- [ ] **30. Gérer les mouvements sur 2 tours** — drone "en transit", occupe la connexion, arrive au tour suivant
- [ ] **31. Afficher les drones en transit** — format : `D1-A-B`

---

## Phase 9 — Optimisation

- [ ] **32. Remplacer BFS par Dijkstra** — `restricted` = coût 2, `priority` = préféré
- [ ] **33. Distribuer les drones** — plusieurs chemins intelligemment
- [ ] **34. Ajouter du scheduling** — décider qui bouge, qui attend
- [ ] **35. Éviter les deadlocks** *(important)*

---

## Phase 10 — Visualisation

- [ ] **36. Terminal coloré** — simple et efficace
- [ ] **37. Améliorer l'affichage** — couleurs, état des hubs, capacité restante
- [ ] **38. GUI (bonus)** — Pygame, Tkinter ou PyQt

---

## Phase 11 — Tests

- [ ] **39. Créer des maps de test** — cas : simple, boucle, blocked, restricted, deadlock, capacité, erreurs parser
- [ ] **40. Tests automatiques** avec pytest

---

## Phase 12 — README *(demandé explicitement)*

- [ ] **41. Documenter** — architecture, algorithmes, structures, simulation, visualisation

---

## Phase 13 — Finition

- [ ] **42. Qualité du code** — `flake8`, `mypy`, exceptions, docstrings
- [ ] **43. Benchmark** — comparer avec les objectifs du sujet

---

## 💡 Pipeline recommandé

```
Parser → Graph → Pathfinding → Simulation → Optimisation → Visualisation
```

> **À éviter** : GUI complexe, optimisation prématurée, algorithme ultra-compliqué dès le début.
