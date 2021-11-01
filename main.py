import requests as req, time, random

from tqdm import tqdm
from py2neo import Graph, Node, Relationship

from modules.constants import *
langs_data = {}

def load_proxy(file):
    with open(file, 'r') as f:
        return list(map(lambda x: {
            'http' : 'socks5://' + x
        }, f.readlines()))    


if __name__ == '__main__':
    username = 'leonvandaal'

    graph      = Graph(NEO4J_HOST, user=NEO4J_LOGIN, password=NEO4J_PASSWORD)
    transition = graph.begin()
    proxy_data = load_proxy('SOCKS5.txt')

    data = {}
    nodes_data = {}
    proxy = proxy_data[random.randint(0, len(proxy_data) - 1)]
    
    for f in tqdm(req.get("https://api.github.com/users/{}/followers".format(username), proxie=proxy).json()):
        user_node = Node('User', name=f['login'])
        transition.create(user_node)

        # Repos owned user
        for repos in req.get(f['repos_url'], proxie=proxy).json():
            repos_node = Node(
                'Repository', 
                name=repos['name'], fullname=repos['full_name'],
                description=repos['description']
                )
            transition.create(repos_node)
            transition.create(Relationship(
                user_node, 'IN_REPOS', repos_node
            ))
            
            # Used langs in repos
            langs = req.get(repos['languages_url'], proxie=proxy).json()
            for lang in langs:
                if lang not in langs_data:
                    langs_data[lang] = Node('Language', name=lang)
                    transition.create(langs_data[lang])

                rel = Relationship(repos_node, 'USE_LANG', langs_data[lang])
                try:
                    rel['procent_usage'] = langs[lang] / sum(list(langs.values()))
                    transition.create(rel) 
                except:
                    pass
                
                
        proxy = proxy_data[random.randint(0, len(proxy_data) - 1)]

        time.sleep(random.randint(6, 13)*10)


        transition.commit()
        transition = graph.begin()