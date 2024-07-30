import argparse
import urllib3
import requests
import yaml
import jinja2
import os

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

headersAuth = {
    'Authorization': 'Bearer '+ str(config['confluence']['api_token']),
}

# Fonction pour obtenir les informations d'une page
def get_page_info(page_id):
    url = f"{config['confluence']['url']}/rest/api/content/{page_id}?expand=ancestors"
    response = requests.get(url, headers=headersAuth,verify=False)
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
                "url": f"{config['confluence']['url']}{page_info['_links']['webui']}"
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
    url = f"{config['confluence']['url']}/rest/api/content?spaceKey={config['confluence']['space']}&limit=100&start={start}"
    #response = requests.get(url, auth=HTTPBasicAuth(username, api_token),verify=False)
    response = requests.get(url, headers=headersAuth,verify=False)
    if response.status_code != 200:
        print(f"Failed to retrieve pages: {response.status_code}")
        break
    
    pages = response.json()
    if not pages['results']:
        break

    for page in pages['results']:
        #print(f"Title: {page['title']} - URL: {confluence_url}{page['_links']['webui']}")
        page_hierarchy = get_page_hierarchy(page['id'])
        parent=[]
        for pageH in page_hierarchy:
          #print(f"Parent: {pageH['title']} - URL: {pageH['url']}")
          parent.insert(0,pageH['title'])
        #print(f"Parent: {','.join(parent)}")
        print(f"{page['title']},{config['confluence']['url']}{page['_links']['webui']},{','.join(parent)}")

    start += 100

