# Site personnel — Gregory Faraut

Sources Quarto de https://gfaraut.github.io. Chaque page est un fichier `.qmd`, c'est-à-dire
du Markdown avec un petit en-tête entre deux lignes `---`.

## Modifier le site

### Petite modification : directement sur GitHub, sans rien installer

1. Ouvrir le fichier sur https://github.com/gfaraut/gfaraut.github.io (par exemple `team.qmd`).
2. Cliquer sur le crayon (*Edit this file*), modifier, puis *Commit changes*.
3. Le site est reconstruit et mis en ligne en deux à trois minutes. Suivi : onglet *Actions*
   (pastille verte = en ligne ; rouge = erreur, le détail s'affiche en cliquant dessus).

### Modification plus importante : en local, avec aperçu

```bash
git pull                      # récupérer la dernière version
quarto preview                # aperçu dans le navigateur, mis à jour à chaque enregistrement
git add -A
git commit -m "Ce que j'ai changé"
git push                      # publication automatique
```

`quarto render` construit le site complet dans `_site/` (sans le publier) ;
`PUBS_REFRESH=1 quarto render` force la relecture des publications sur HAL et OpenAlex.

## Tâches courantes

| Je veux… | Où | Comment |
|---|---|---|
| ajouter ou déplacer un doctorant, un stagiaire | `team.qmd` | copier un bloc de deux lignes ; mode d'emploi en tête du fichier |
| ajouter un projet, passer un projet en « Past » | `projects.qmd` | copier un bloc de deux ou trois lignes ; budget global seulement, ni rôle ni part LURPA ; mode d'emploi en tête du fichier |
| ajouter un jury de thèse, une conférence invitée, un comité, une expertise | `service.qmd` | un bloc par activité, du plus récent au plus ancien ; mode d'emploi en tête du fichier ; pas de compteurs (DORA) |
| publier une offre de stage ou de thèse | `data/offers.yml` | modèle en tête du fichier ; l'offre disparaît seule après sa date `expires` |
| ajouter une publication | rien à faire | déposée sur HAL (ou référencée par OpenAlex), elle apparaît à la reconstruction du lundi ; pour l'avoir tout de suite : *Actions* → *Publish site* → *Run workflow* |
| ajouter une publication pas encore référencée | `data/publications-manual.yml` | modèle en tête du fichier ; supprimer l'entrée quand l'article arrive sur HAL |
| informations JCR et quartile SJR des revues | `data/journals.csv` | conservées mais **non affichées** (choix DORA, voir plus bas) |
| masquer une publication attribuée à tort par OpenAlex | `scripts/publications.py` | ajouter son DOI dans `EXCLUDE_DOIS` |
| modifier la présentation de la recherche | `research.qmd` | vue d'ensemble et résumé de chaque thème ; cartes correspondantes dans `index.qmd` (bloc `{.research-overview}`) |
| modifier un thème, une publication choisie | `research/identification.qmd`, `research/detection.qmd`, `research/control.qmd` | une page par thème ; une phrase d'apport et une étiquette de domaine par publication ; mode d'emploi en tête de `research/identification.qmd` |
| modifier la figure de la recherche | `assets/img/research-loop.svg` | Inkscape ou éditeur de texte ; reprise telle quelle sur l'accueil, la page Research et les pages de thème |
| modifier la biographie, les anciens postes | `index.qmd` | |
| modifier les mots-clés de l'accueil | `index.qmd` | bloc `{.keywords}` : un mot-clé par ligne ; garder la même liste que sur ORCID et HAL |
| modifier le CV, le contact, l'enseignement | `cv.qmd`, `contact.qmd`, `teaching.qmd` | responsabilités pédagogiques : `teaching.qmd` ; activités de service : `service.qmd` seulement (le CV y renvoie) |
| modifier les logos des institutions | `index.qmd` (bloc `{.hero-logos}`) et `_quarto.yml` (`page-footer:`) | fichiers officiels dans `assets/`, à ne pas retoucher ; tailles dans `styles.css` |
| ajouter une image | `assets/img/` | puis dans la page : `![](assets/img/mon-image.jpg)` |
| ajouter une page | nouveau fichier `ma-page.qmd` | en tête : `pagetitle: "Gregory Faraut – …"` (titre de l'onglet et des résultats de recherche, Quarto ajoute « – ENS Paris-Saclay, LURPA ») et `description:` (environ 150 caractères, lue par les moteurs de recherche, non affichée) ; puis l'ajouter au menu, section `navbar:` de `_quarto.yml` |
| modifier le titre ou la description d'une page dans les moteurs de recherche | en tête de chaque `.qmd` | `pagetitle:` (commencer par « Gregory Faraut – ») et `description:` |
| ajouter un profil (sameAs), un thème pour les moteurs de recherche | `_includes/person-jsonld.html` | fiche « Person » schema.org de l'accueil, invisible pour les visiteurs |
| coller une balise de vérification Google Search Console | `_includes/head-meta.html` | le site est déjà vérifié par le fichier `googlefc2dcb7edf7908b6.html` |

### Rappel Markdown

```markdown
## Titre de section
**gras**, *italique*, [texte du lien](https://adresse)
- élément de liste
<!-- commentaire : invisible sur le site -->
```

### À ne pas modifier

- `_site/` et `.quarto/` : produits par Quarto, recréés à chaque rendu (et non versionnés).
- `data/publications.yml` : réécrit à chaque construction par `scripts/publications.py`.
- `_extensions/lurpa/` : socle commun aux cours et présentations LURPA.

## Fonctionnement

| Chemin | Rôle |
|---|---|
| `_quarto.yml` | configuration du site (menu, pied de page, format) |
| `*.qmd` | une page par fichier |
| `scripts/publications.py` | avant chaque rendu : lit HAL puis OpenAlex, uniformise le nom (« Gregory Faraut »), date et trie les publications, écrit `data/publications.yml` et liste dans le journal les articles à déposer sur HAL |
| `data/publications-manual.yml` | publications ajoutées à la main |
| `data/journals.csv` | revues : indexation JCR et quartile SJR (non affichés) |
| `data/offers.yml` | offres de stage et de thèse, avec date d'expiration |
| `_templates/publications.ejs` | mise en forme de la liste des publications |
| `_templates/recent-publications.ejs` | les 3 dernières publications, sur l'accueil |
| `_templates/offers.ejs` | offres en cours, sur la page Supervision (écarte les offres expirées) |
| `styles.css` | règles propres au site (le thème vient du socle `lurpa`) |
| `_extensions/lurpa/` | socle Quarto LURPA (format `lurpa-html`) |
| `research/` | une page par thème de recherche |
| `_includes/` | balises ajoutées dans l'en-tête des pages : `head-meta.html` (toutes les pages), `person-jsonld.html` (accueil) |
| `assets/` | images et logos ; `assets/img/research-loop.svg` : figure de la recherche, aux liens cliquables |
| `.github/workflows/publish.yml` | construction et mise en ligne : à chaque envoi sur `main` et chaque lundi |
| `googlefc2dcb7edf7908b6.html` | vérification Google Search Console, à garder |

Les anciennes adresses (`content/*.html`) redirigent vers les nouvelles pages grâce aux
`aliases:` placés en tête de chaque page.

## Évaluation de la recherche (DORA)

Le site suit la [déclaration DORA](https://sfdora.org/read/), signée par l'Université
Paris-Saclay en 2022 : ni indicateur de revue (facteur d'impact, quartile), ni nombre de
citations. Chaque publication choisie des pages de thème (`research/`) est présentée par ce qu'elle apporte.
Les informations JCR et SJR restent dans `data/journals.csv` pour les dossiers qui les
exigent ; `_templates/publications.ejs` explique comment les réafficher.

