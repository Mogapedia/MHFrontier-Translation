# Guide de style FR — MHFrontier

Conventions de rédaction pour la traduction française de MHFrontier.
S'applique à tout `target` dans `translations/fr/**/*.csv`.

## 1. Adresse au joueur

- **Tutoyer** le joueur (« Tu as obtenu un objet rare ! »).
  Cohérent avec les MH officiels FR récents et le ton communautaire.
- Les PNJ peuvent vouvoyer le joueur si le contexte le justifie
  (gardes de guilde formels, dialogues de cour) — décision au cas
  par cas, signaler dans le commit.

## 2. Typographie française

- Guillemets français : **« texte »** (avec espaces insécables si
  possible). Jamais `"…"` sauf à l'intérieur de balises de contrôle.
- Ligature **œ** (cœur, sœur, œuf) — jamais `oe`.
- Apostrophe courbe `'` non requise ; l'apostrophe droite `'` est
  acceptable car le moteur ne rend pas toujours les caractères Unicode
  étendus.
- Espaces avant `:` `;` `!` `?` `»` : **omettre** dans les chaînes UI
  courtes (contraintes de largeur écran). Conserver dans les
  descriptions longues si la place le permet.
- Majuscules accentuées : **À É È** sont OK et préférables.

### 2bis. Accents : règle pour ce repo, et limitation actuelle du jeu

**Règle pour les CSV de ce repo : écrire le français avec ses
accents normaux** (é è ê à â ô ù û î ç œ « »). Les CSV sont la
**source de vérité** et doivent rester en français propre, lisible,
et indépendant des limitations actuelles du moteur. Toujours éditer
en **UTF-8** (par défaut sur VS Code, Python, etc. ; **éviter
Excel** qui corrompt silencieusement les accents).

**Limitation à connaître** (ne change pas la règle ci-dessus) :
au moment où ces lignes sont écrites, le jeu utilise des **fontes
custom** qui n'embarquent pas les glyphes latins accentués FR — les
accents écrits tels quels dans le binaire s'affichent en glyphe
manquant ou cassé. Cette limitation est **côté outils en aval**
(FrontierTextHandler pour l'import binaire, mhf-outpost pour les
payloads du launcher) et n'a pas à polluer ce repo. Deux pistes
pour la lever, à traiter dans les projets concernés et non ici :

1. **Pliage ASCII au moment de l'application** (court terme) :
   l'outil qui injecte les CSV dans le `.bin` rabat les caractères
   accentués sur leur équivalent ASCII (`é`→`e`, `œ`→`oe`, `«`→`"`,
   etc.) avant l'écriture. C'est lossy mais désactivable.
2. **Extension des fontes custom** (cible long terme) : ajouter les
   glyphes manquants à la fonte du jeu, ce qui rend le pliage
   inutile. Demande du travail de RE sur le format de fonte.

En attendant, **le contributeur traduction n'a rien à faire de
spécial** : il écrit du français correct dans le CSV, et c'est aux
outils en aval de décider quoi en faire au moment du build. Si ton
test en jeu montre des glyphes cassés, **c'est un bug à remonter
sur l'outil de build, pas une raison d'éditer le CSV.**

## 3. Longueur & contraintes UI

Le jeu a été conçu pour du texte japonais : un caractère JP occupe
visuellement la place d'environ deux caractères latins. Les boîtes
de l'UI (menus, items, boutons, infobulles) sont **dimensionnées
pour la version JP**. Quand une chaîne dépasse, le moteur **ne
tronque pas et ne renvoie pas à la ligne** : le texte **déborde**
hors de sa boîte et chevauche les éléments voisins (autres
libellés, bordures, icônes). Le résultat est lisible mais visuellement
cassé, et il n'y a aucun avertissement à la compilation.

Conséquences pratiques pour le traducteur :

- **Compter les caractères source, pas les mots.** Une chaîne JP
  de 8 caractères = ~16 caractères latins maximum, pas davantage.
- **Règle empirique** : ne pas dépasser **1.3× la longueur EN** si
  une version EN existe (l'EN a déjà subi la même contrainte et
  sert de plafond raisonnable). Sans EN, viser **≤ 2× le nombre
  de caractères JP**.
- **Abréger plutôt que laisser déborder.** « Méga potion » plutôt
  que « Potion méga-puissante » ; « Fusarb. léger » est acceptable
  dans une infobulle si « Fusarbalète léger » déborde sur l'élément
  voisin.
- **Tester en jeu** les chaînes à forte visibilité (noms d'armes,
  menus principaux) avant de figer la traduction — c'est le seul
  moyen fiable de repérer un débordement qui chevauche un libellé
  ou une icône adjacente.
- Pour les descriptions multi-lignes, **respecter le nombre de
  segments** délimités par les marqueurs `{j}` (voir §5).
  Chaque segment correspond à une ligne à l'écran avec sa propre
  largeur maximale — ne pas « rééquilibrer » en déplaçant du texte
  d'un segment à l'autre.

## 4. Casse des noms propres et objets

- Noms d'armes / armures / objets : **première lettre en majuscule**,
  reste en minuscules sauf nom propre. Ex : `Épée d'os`, `Casque en
  fer`, `Potion`.
- Noms de monstres : casse Mogapédia (Rathalos, Tigrex, Espinas).
- Noms de quêtes : majuscule initiale uniquement, sauf noms propres.

## 5. Codes de contrôle — RÈGLE CRITIQUE

Les marqueurs `{j}` (saut de ligne), `{cNN}` / `{/c}` (couleur),
`{K...}`, `{i...}`, `{u...}` et autres codes binaires intégrés au
texte **ne doivent JAMAIS être traduits, supprimés, ni réordonnés**.
FTH ≥ 1.6.0 reconstruit les offsets binaires au moment de
l'application à partir du nombre et de l'ordre des marqueurs — le
**nombre** et l'**ordre** doivent rester identiques à la source.

- Copier les marqueurs tels quels depuis la colonne `source`.
- Le texte FR s'insère **entre** les marqueurs, en respectant la
  segmentation visuelle (chaque `{j}` = un saut de ligne à l'écran).
- Ne pas ajouter de marqueurs absents de la source.
- Les codes `~A00`, `~B03`… (tilde, lettre, deux chiffres) sont des
  **substitutions** : le jeu les remplace par un nom de touche ou un
  numéro d'emplacement (« ~B00 ou ~B03 : ranger le fusarbalète »). Les
  recopier tels quels ; `validate.py` refuse une traduction qui en perd un.
- Les lignes contenant **uniquement** des codes de contrôle
  (~6 643 lignes recensées) doivent rester avec `target` vide.

## 6. Lignes spéciales à laisser vides

- Lignes `dummy` dans `dat/items/source.csv` (1 211 entrées) :
  `target` vide, ne s'affichent pas en jeu.
- Lignes ne contenant que ponctuation ou séparateurs (`−−−−−−`,
  espaces, points) : recopier la source telle quelle.
- Lignes dont la `source` est un nom interne en anglais
  (`Z3P_item_089`) : `target` vide, ce sont des emplacements inutilisés.

## 7. Cohérence terminologique

- Toujours consulter `docs/glossary.fr.md` avant de traduire un
  terme récurrent.
- Si un terme manque au glossaire et apparaît plusieurs fois,
  **ajouter l'entrée au glossaire d'abord**, puis traduire.
- Réutiliser les `target` déjà présents dans d'autres CSV pour
  une `source` identique (mémoire de traduction implicite).

## 8. Ton et registre

- Descriptions d'objets / d'armes : ton **factuel et concis**,
  pas de fioriture marketing. Style proche d'un manuel de jeu.
- Dialogues PNJ et scénario : conserver le **ton** du japonais
  (formel, familier, archaïque) ; l'anglais existant est souvent
  trop neutre — s'autoriser à remonter à la source JP en cas de
  doute.
- Pas d'humour ajouté ni de références culturelles FR plaquées.
  La saveur reste japonaise/médiévale-fantastique.

## 9. Workflow par section

1. Lire `docs/glossary.fr.md` et cette page.
2. Choisir **une seule section** (un seul fichier CSV) à la fois.
3. Pré-remplir les `target` triviaux par mémoire de traduction
   (exact match sur d'autres CSV).
4. Traduire les lignes restantes en respectant codes de contrôle
   et longueurs.
5. Lancer `python scripts/validate.py` avant tout commit.
6. (Optionnel) Construire le binaire avec `scripts/build_bins.py`
   et tester en jeu sur les sections à forte visibilité.

## 10. Quand demander une revue humaine

- Dialogues de scénario, monologues PNJ, textes de quêtes narratifs.
- Tout texte où la nuance culturelle compte plus que la fidélité
  littérale.
- Termes ajoutés au glossaire (validation par un membre Mogapédia).
