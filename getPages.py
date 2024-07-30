import argparse
import urllib3
import requests
import yaml
import jinja2
import os

# Disable warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Argument parser pour les arguments de la ligne de commande
parser = argparse.ArgumentParser(description='Scan Confluence Space')
parser.add_argument("-c", "--config", help="config file", type=argparse.FileType('r'), default="../config.yml")
args = parser.parse_args()

# Lire le fichier YAML
yaml_config = yaml.safe_load(args.config)
args.config.close()  # Fermer le fichier après lecture

# Obtenir le répertoire du fichier de configuration pour le FileSystemLoader de Jinja2
config_dir = os.path.dirname(args.config.name)

# Configurer l'environnement Jinja2 avec le répertoire du fichier de configuration
env = jinja2.Environment(loader=jinja2.FileSystemLoader(searchpath=config_dir))

# Charger le template Jinja2 depuis le chemin du fichier
template = env.get_template(os.path.basename(args.config.name))

# Rendre le template avec le contenu YAML
rendered_config = template.render(**yaml_config)

# Charger le contenu YAML rendu comme un dictionnaire
config = yaml.safe_load(rendered_config)

# Headers
headersAuth = {
    'Authorization': 'Bearer '+ str(config['confluence']['api_token']),
}

# Variables
url = config['confluence']['url']
space = config['confluence']['space']
csv_separator = ";"

# Fonction pour obtenir les informations d'une page
def get_page_info(page_id):
    wurl = f"{url}/rest/api/content/{page_id}?expand=ancestors"
    response = requests.get(wurl, headers=headersAuth,verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to retrieve page info: {response.status_code}")
        return None

# Fonction pour obtenir la hiérarchie des pages jusqu'à la racine
def get_page_hierarchy(page_id):
    hierarchy = []
    while page_id:
        page_info = get_page_info(page_id)
        if page_info:
            hierarchy.append({
                "id": page_info['id'],
                "title": page_info['title'],
                "url": f"{url}{page_info['_links']['webui']}"
            })
            if page_info['ancestors']:
                page_id = page_info['ancestors'][-1]['id']
            else:
                break
        else:
            break
    return hierarchy


start = 0
while True:
    wurl = f"{url}/rest/api/content?spaceKey={space}&limit=100&start={start}"
    response = requests.get(wurl, headers=headersAuth,verify=False)
    if response.status_code != 200:
        print(f"Failed to retrieve pages: {response.status_code}")
        break
    
    pages = response.json()
    if not pages['results']:
        break

    for page in pages['results']:
        page_hierarchy = get_page_hierarchy(page['id'])
        parent=[]
        for pageH in page_hierarchy:
          parent.insert(0,pageH['title'])
        #print(f"{page['title']};{url}{page['_links']['webui']};{';'.join([]+[]+parent)}")
        print(f"{csv_separator.join([page['title'],page['_links']['webui']]+parent)}")

    start += 100

SystemExit(0)
