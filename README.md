# Memimto server

Doit-être utiliser avec [MemIMTo Client](https://github.com/zyioump/memimto_client)

Attention le système d'identification de visage à partir d'une nouvelle image ne fonctionne pas sur la branche nvidia.

## Configuration
Choisissez des mots de passe pour la base de donnée mariadb dans `docker-compose.yaml` ou dans `docker-compose.yaml.nvidia` si vous utilisez une carte graphique nvidia. Dans ce cas n'oublier pas d'installer les drivers ainsi que Cuda et CuDNN.

Copier la configuration par default et éditer la :
```bash
cp .env.example .env
vim .env
```
## Docker compose
Si vous souhaiter utilisez une carte graphique nvidia, remplacez le fichier `docker-compose.yaml` par `docker-compose.yaml.nvidia`

Puis vous pouvez démarrer les conteneurs à l'aide de docker :

```bash
docker compose up
```

## Enpoint

- `/login` **POST** avec en donnée un formulaireHTML ayant comme champ name et password
- `/albums` **GET** retourne la liste des albums disponibles
- `/album/<int:id>/` **GET** retourne les image d'un album en particulier
- `/album/<int:album_id>/cluster/<int:cluster>` **GET** retourne les image relatif un cluster et à un album
- `/album/<int:album_id>/find_cluster` **POST** avec en donnée une image en base64, retourne le cluster de la personne identifier sur l'image.
- `/image/<name>` **GET** retourne une l'image demandé
- `/upload` **POST** avec comme Header Filename, Chunkstart et Chunksize et en donnée le chunk du fichier à uploader, quand l'upload est terminé le regroupement des visage se lance automatiquement
- `/recluster/<int:album_id>` **GET** permet de relancer la procédure de regroupement de visage sur un album (les encodings sont déjà enregistré donc cette opération va relativement vite)
- `/delete/<int:album_id>` **GET** permet de supprimer un album