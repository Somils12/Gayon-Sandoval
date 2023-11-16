# -*- coding: utf-8 -*-

import os
import json
import bz2
import networkx as nx
import json
import getopt
import sys
import os
import shutil
from datetime import datetime

def encontrar_archivos_json_bz2(directorio, fecha_inicial=None, fecha_final=None):
    archivos_encontrados = []
    for ruta_actual, carpetas, archivos in os.walk(directorio):
        for archivo in archivos:
            if archivo.endswith('.json.bz2'):
                ruta_archivo = os.path.join(ruta_actual, archivo)
                fecha_archivo = obtener_fecha_desde_nombre(archivo)
                if (not fecha_inicial or fecha_archivo >= fecha_inicial) and (not fecha_final or fecha_archivo <= fecha_final):
                    archivos_encontrados.append(ruta_archivo)
    return archivos_encontrados

def obtener_fecha_desde_nombre(nombre_archivo):
    # Simulación para extraer la fecha desde el nombre del archivo
    fecha_str = nombre_archivo.split('.')[0]
    partes_fecha = fecha_str.split('-')
    return '-'.join(partes_fecha)

# Directorio raíz
directorio_raiz = '.'  # Directorio raíz

# Pedir al usuario que ingrese el directorio del que desea copiar los archivos .json.bz2
directorio_a_copiar = input("Ingrese el directorio relativo carpeta/subcarpeta/ ")

directorio_absoluto = os.path.abspath(directorio_a_copiar)

# Verificar si el directorio ingresado existe
if os.path.exists(directorio_absoluto):
    # Pedir al usuario las fechas inicial y final (opcional)
    fecha_inicial = None
    fecha_final = None

    # Convertir las fechas ingresadas a un formato adecuado si fueron ingresadas
    if fecha_inicial:
        fecha_inicial = '-'.join(fecha_inicial.split('-')[::-1])
    if fecha_final:
        fecha_final = '-'.join(fecha_final.split('-')[::-1])

    # Solicitar al usuario el nombre del archivo que contiene los hashtags
    nombre_archivo_hashtags = input("Ingrese el nombre del archivo de texto con los hashtags (ignorar si no aplica): ")
    if nombre_archivo_hashtags:
        if not nombre_archivo_hashtags.endswith('.txt'):
            nombre_archivo_hashtags += '.txt'
            
    # Crear el directorio de destino
    directorio_destino = os.path.join(directorio_raiz, 'datos_copiados')
    if not os.path.exists(directorio_destino):
        os.makedirs(directorio_destino)

    # Encontrar archivos .json.bz2 en el directorio ingresado por el usuario según las fechas proporcionadas
    archivos_json_bz2 = encontrar_archivos_json_bz2(directorio_absoluto, fecha_inicial, fecha_final)

    # Copiar archivos al directorio de destino
    for archivo in archivos_json_bz2:
        nombre_archivo = os.path.basename(archivo)
        nombre_sin_extension = os.path.splitext(nombre_archivo)[0]
        extension = os.path.splitext(nombre_archivo)[1]

        # Verificar si el archivo ya existe en el directorio destino
        contador = 1
        nuevo_nombre = nombre_archivo
        while os.path.exists(os.path.join(directorio_destino, nuevo_nombre)):
            nuevo_nombre = f"{nombre_sin_extension}_{contador}{extension}"
            contador += 1

        shutil.copy(archivo, os.path.join(directorio_destino, nuevo_nombre))

    # Realizar el procedimiento necesario con los archivos copiados en directorio_destino
    # (Aquí puedes agregar el procedimiento que necesites hacer)

    # Eliminar los archivos copiados después del procedimiento
else:
    print("El directorio especificado no existe.")

directorio = "./datos_copiados/"
archivo_salida = "merged_output.json"
archivo_hashtags =  nombre_archivo_hashtags

# Cargar los hashtags del archivo
hashtags_a_buscar = []
if os.path.exists(archivo_hashtags):
    with open(archivo_hashtags, 'r') as file:
        hashtags_a_buscar = [line.strip() for line in file.readlines()]

tweets_data = []

fecha_inicial_str = input("Ingrese la fecha inicial (dd-mm-aaaa) o presione Enter para omitir: ")
fecha_final_str = input("Ingrese la fecha final (dd-mm-aaaa) o presione Enter para omitir: ")

# Convertir las fechas ingresadas a un formato adecuado si fueron ingresadas
if fecha_inicial_str:
    fecha_inicial = datetime.strptime(fecha_inicial_str, "%d-%m-%Y").date()
if fecha_final_str:
    fecha_final = datetime.strptime(fecha_final_str, "%d-%m-%Y").date()

for archivo_bz2 in os.listdir(directorio):
    if archivo_bz2.endswith(".bz2"):
        ruta_archivo = os.path.join(directorio, archivo_bz2)

        with bz2.BZ2File(ruta_archivo, 'rb') as archivo_comprimido:
            contenido_descomprimido = archivo_comprimido.read().decode('utf-8')
            tweets = contenido_descomprimido.strip().split('\n')

            for tweet in tweets:
                try:
                    datos_tweet = json.loads(tweet)

                    # Convertir la fecha del tweet al formato deseado
                    fecha_tweet_str = datos_tweet.get("created_at", "")
                    if fecha_tweet_str:
                        fecha_tweet = datetime.strptime(fecha_tweet_str, "%a %b %d %H:%M:%S +0000 %Y").date()

                    # Verificar si el tweet contiene al menos uno de los hashtags buscados
                    if hashtags_a_buscar:
                        tweet_contiene_hashtag = any(hashtag['text'] in hashtags_a_buscar for hashtag in datos_tweet.get("entities", {}).get("hashtags", []))
                        if not tweet_contiene_hashtag:
                            continue  # Si no contiene ninguno de los hashtags, pasar al siguiente tweet

                    # Verificar si la fecha del tweet está dentro del rango especificado
                    if fecha_inicial and fecha_final:
                        if not (fecha_inicial <= fecha_tweet <= fecha_final):
                            continue  # Si la fecha está fuera del rango, pasar al siguiente tweet


                    tweet_filtrado = {
                        "created_at": datos_tweet.get("created_at", None),
                        "id_str": datos_tweet.get("id_str", None),
                        "text": datos_tweet.get("text", None),
                        "user": {
                            "id": datos_tweet.get("user", {}).get("id", None),
                            "name": datos_tweet.get("user", {}).get("name", None),
                            "screen_name": datos_tweet.get("user", {}).get("screen_name", None),
                            "location": datos_tweet.get("user", {}).get("location", None),
                            "url": datos_tweet.get("user", {}).get("url", None),
                            "description": datos_tweet.get("user", {}).get("description", None),
                        },
                        "place": {},
                        "entities": {
                            "hashtags": [],
                            "urls": [],
                            "user_mentions": []
                        }
                    }

                    if "urls" in datos_tweet.get("entities", {}):
                        for url_info in datos_tweet["entities"]["urls"]:
                            url_entry = {
                                "url": url_info.get("url", None),
                                "unwound": {
                                    "url": url_info.get("unwound", {}).get("url", None),
                                    "title": url_info.get("unwound", {}).get("title", None),
                                }
                            }
                            tweet_filtrado["entities"]["urls"].append(url_entry)

                    if "user_mentions" in datos_tweet.get("entities", {}):
                        for mention_info in datos_tweet["entities"]["user_mentions"]:
                            mention_entry = {
                                "id": mention_info.get("id", None),
                                "name": mention_info.get("name", None),
                                "screen_name": mention_info.get("screen_name", None),
                            }
                            tweet_filtrado["entities"]["user_mentions"].append(mention_entry)

                    # Extraer hashtags
                    if "hashtags" in datos_tweet.get("entities", {}):
                        for hashtag_info in datos_tweet["entities"]["hashtags"]:
                            hashtag_entry = {
                                "text": hashtag_info.get("text", None),
                            }
                            tweet_filtrado["entities"]["hashtags"].append(hashtag_entry)

                    tweets_data.append(tweet_filtrado)

                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file {ruta_archivo}: {e}")

with open(archivo_salida, 'w', encoding='utf-8') as archivo_salida:
    json.dump(tweets_data, archivo_salida, ensure_ascii=False, indent=2)

# Cargar el archivo JSON
with open('merged_output.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Diccionario para almacenar los retweets por usuario
retweet_data = {}

# Procesar los retweets para construir la estructura de datos
for tweet in data:
    text = tweet.get('text')  # Obtener el texto del tweet
    if text and text.startswith('RT @'):  # Verificar si hay texto y si indica un retweet
        retweeted_user = text.split()[1][1:]  # Obtener el nombre del usuario retuiteado
        retweeting_user = tweet['user']['screen_name']

        if 'retweeted_status' in tweet:
            tweet_id = tweet['retweeted_status']['id_str']
        else:
            tweet_id = tweet['id_str']  # Si es un tweet original, usar su propio ID

        if retweeted_user not in retweet_data:
            retweet_data[retweeted_user] = {
                'receivedRetweets': 0,
                'tweets': {}
            }

        retweet_data[retweeted_user]['receivedRetweets'] += 1

        if tweet_id not in retweet_data[retweeted_user]['tweets']:
            retweet_data[retweeted_user]['tweets'][tweet_id] = {'retweetedBy': []}

        retweet_data[retweeted_user]['tweets'][tweet_id]['retweetedBy'].append(retweeting_user)

# Crear la estructura final del JSON
final_retweets = []

for user, user_data in retweet_data.items():
    user_info = {
        'username': user,
        'receivedRetweets': user_data['receivedRetweets'],
        'tweets': []
    }
    for tweet_id, retweeted_by in user_data['tweets'].items():
        tweet_info = {
            'tweetId': tweet_id,  # Corregido: Separar el formato del ID del tweet
            'retweetedBy': retweeted_by['retweetedBy']
        }
        user_info['tweets'].append(tweet_info)
    final_retweets.append(user_info)

final_json = {'retweets': final_retweets}

# Guardar el JSON en el archivo rt.json
with open('rt.json', 'w', encoding='utf-8') as outfile:
    json.dump(final_json, outfile, indent=4, ensure_ascii=False)

# Cargar el archivo JSON de retweets
with open('rt.json', 'r', encoding='utf-8') as file:
    rt_data = json.load(file)

# Crear un grafo dirigido
G = nx.DiGraph()

# Procesar los retweets para construir el grafo
for user_info in rt_data['retweets']:
    username = user_info['username']
    received_retweets = user_info['receivedRetweets']

    # Añadir nodo de usuario al grafo
    G.add_node(username, received_retweets=received_retweets)

    # Si hay tweets retuiteados por el usuario
    if 'tweets' in user_info:
        for tweet in user_info['tweets']:
            tweet_id = tweet['tweetId']
            retweeted_by = tweet['retweetedBy']

            # Conectar usuarios que retuitearon el mismo tweet
            for retweeter in retweeted_by:
                G.add_edge(retweeter, username)

# Guardar el grafo en formato GEXF
nx.write_gexf(G, 'rt.gexf')





# Cargar el archivo JSON
with open('merged_output.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Diccionario para almacenar las menciones por usuario
mention_data = {}

# Procesar los tweets en busca de menciones
for tweet in data:
    user_mentioned = tweet.get('entities', {}).get('user_mentions')
    if user_mentioned:  # Verificar si hay menciones en el tweet
        for mention in user_mentioned:
            mentioned_user = mention['screen_name']
            mention_by_user = tweet['user']['screen_name']
            tweet_id = tweet['id_str']

            if mentioned_user not in mention_data:
                mention_data[mentioned_user] = {
                    'receivedMentions': 0,
                    'mentions': []
                }

            mention_data[mentioned_user]['receivedMentions'] += 1

            mention_info = {
                'mentionBy': mention_by_user,
                'tweets': [tweet_id]
            }

            # Si ya hay menciones previas del usuario
            existing_mentions = mention_data[mentioned_user]['mentions']
            user_mention = next((item for item in existing_mentions if item['mentionBy'] == mention_by_user), None)
            if user_mention:
                user_mention['tweets'].append(tweet_id)
            else:
                mention_data[mentioned_user]['mentions'].append(mention_info)

# Ordenar los usuarios por el total de menciones recibidas
sorted_mention_data = sorted(mention_data.items(), key=lambda x: x[1]['receivedMentions'], reverse=True)

# Crear la estructura final del JSON
final_mentions = []

for user, user_data in sorted_mention_data:
    mentions_info = {
        'username': user,
        'receivedMentions': user_data['receivedMentions'],
        'mentions': user_data['mentions']
    }
    final_mentions.append(mentions_info)

final_json = {'mentions': final_mentions}

# Guardar el JSON en el archivo mencion.json
with open('mencion.json', 'w', encoding='utf-8') as outfile:
    json.dump(final_json, outfile, indent=4, ensure_ascii=False)

# Cargar los datos desde el archivo mencion.json
with open('mencion.json', 'r', encoding='utf-8') as file:
    mention_data = json.load(file)

# Crear un grafo dirigido
mention_graph = nx.DiGraph()

# Iterar sobre cada usuario y sus menciones
for user_mention in mention_data['mentions']:
    username = user_mention['username']
    mentions = user_mention['mentions']

    # Agregar nodos al grafo
    mention_graph.add_node(username)

    # Agregar las menciones como aristas
    for mention in mentions:
        mention_by = mention['mentionBy']
        mention_graph.add_edge(mention_by, username)

# Verificar si el grafo tiene componentes conectados (usuarios no mencionados)
isolated_nodes = list(nx.isolates(mention_graph))

# Eliminar usuarios no mencionados
mention_graph.remove_nodes_from(isolated_nodes)

# Exportar el grafo a un archivo GEXF
nx.write_gexf(mention_graph, 'mencion.gexf')





# Cargar el archivo JSON
with open('rt.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Crear una lista de todos los usuarios presentes
all_users = set()
for retweet_info in data['retweets']:
    all_users.add(retweet_info['username'])

# Crear un diccionario para mantener un registro de quién retuiteó a quién
retweets_dict = {user: set() for user in all_users}

# Llenar el diccionario con los retweets por cada usuario
for retweet_info in data['retweets']:
    username = retweet_info['username']
    tweets = retweet_info.get('tweets', {})

    # Comprobar si 'tweets' es una lista o un diccionario
    if isinstance(tweets, list):
        for tweet in tweets:
            retweeted_by = tweet.get('retweetedBy', [])
            retweets_dict[username].update(retweeted_by)
    else:
        for tweet_id, retweeted_by in tweets.items():
            retweets_dict[username].update(retweeted_by['retweetedBy'])

# Encontrar usuarios comunes que retuitearon a cualquier par de usuarios
usuarios_comunes_por_par = {}
for user1 in all_users:
    for user2 in all_users:
        if user1 != user2:
            common_retweeters = retweets_dict[user1].intersection(retweets_dict[user2])
            if len(common_retweeters) > 0:
                usuarios_comunes_por_par[(user1, user2)] = list(common_retweeters)

# Crear una lista de coretweets en el formato requerido
coretweets_list = []
for usuarios, retweeters in usuarios_comunes_por_par.items():
    coretweet = {
        "authors": {
            "u1": usuarios[0],
            "u2": usuarios[1]
        },
        "totalCoretweets": len(retweeters),
        "retweeters": retweeters
    }
    coretweets_list.append(coretweet)

# Ordenar los coretweets de mayor a menor por el total de retweeters
coretweets_list = sorted(coretweets_list, key=lambda x: x['totalCoretweets'], reverse=True)

# Crear un diccionario con la lista de coretweets
coretweets_dict = {"coretweets": coretweets_list}

# Guardar los datos en un archivo corrtw.json
with open('corrtw.json', 'w', encoding='utf-8') as file:
    json.dump(coretweets_dict, file, indent=4)

# Cargar los datos de coretweets desde corrtw.json
with open('corrtw.json', 'r', encoding='utf-8') as file:
    coretweets_data = json.load(file)

# Crear un grafo dirigido
G = nx.DiGraph()

# Agregar nodos y aristas al grafo
for coretweet in coretweets_data['coretweets']:
    u1 = coretweet['authors']['u1']
    u2 = coretweet['authors']['u2']
    retweeters = coretweet['retweeters']

    G.add_edge(u1, u2, weight=len(retweeters))

# Exportar el grafo a un archivo corrtw.gexf
nx.write_gexf(G, 'corrtw.gexf')

carpeta_a_eliminar = os.path.join(directorio_destino)
if os.path.exists(carpeta_a_eliminar):
    shutil.rmtree(carpeta_a_eliminar)
