import os
import json
import bz2
import networkx as nx
import getopt
import sys
import shutil
from datetime import datetime
import time
from mpi4py import MPI



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


def encontrar_archivos(directorio_a_copiar,nombre_archivo_hashtags,fecha_inicial_str,fecha_final_str):
    directorio_raiz = '.'  
    directorio_absoluto = os.path.abspath(directorio_a_copiar)
    if os.path.exists(directorio_absoluto):
        fecha_inicial = None
        fecha_final = None
        if fecha_inicial:
            fecha_inicial = '-'.join(fecha_inicial.split('-')[::-1])
        if fecha_final:
            fecha_final = '-'.join(fecha_final.split('-')[::-1])
        directorio_destino = os.path.join(directorio_raiz, 'datos_copiadosp')
        try:
            os.makedirs(directorio_destino)
        except FileExistsError:
            pass
        archivos_json_bz2 = encontrar_archivos_json_bz2(directorio_absoluto, fecha_inicial, fecha_final)
        for archivo in archivos_json_bz2:
            nombre_archivo = os.path.basename(archivo)
            nombre_sin_extension = os.path.splitext(nombre_archivo)[0]
            extension = os.path.splitext(nombre_archivo)[1]
            contador = 1
            nuevo_nombre = nombre_archivo
            while os.path.exists(os.path.join(directorio_destino, nuevo_nombre)):
                nuevo_nombre = f"{nombre_sin_extension}_{contador}{extension}"
                contador += 1
            shutil.copy(archivo, os.path.join(directorio_destino, nuevo_nombre))
    else:
        print("El directorio especificado no existe.")

        

def merged_output(archivo, hashtags_a_buscar, fecha_inicial, fecha_final):
    tweets_data = []
    with bz2.BZ2File(archivo, 'rb') as archivo_comprimido:
        contenido_descomprimido = archivo_comprimido.read().decode('utf-8')
        tweets = contenido_descomprimido.strip().split('\n')
        for tweet in tweets:
            try:
                datos_tweet = json.loads(tweet)
                fecha_tweet_str = datos_tweet.get("created_at", "")
                if fecha_tweet_str:
                    fecha_tweet = datetime.strptime(fecha_tweet_str, "%a %b %d %H:%M:%S +0000 %Y").date()
                hashtags_del_tweet = [hashtag['text'].lower() for hashtag in datos_tweet.get("entities", {}).get("hashtags", [])]
                if hashtags_a_buscar:
                    tweet_contiene_hashtag = any(hashtag in hashtags_a_buscar for hashtag in hashtags_del_tweet)
                    if not tweet_contiene_hashtag:
                        continue
                if fecha_inicial and fecha_final:
                    if not (fecha_inicial <= fecha_tweet <= fecha_final):
                        continue
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
                if "hashtags" in datos_tweet.get("entities", {}):
                    for hashtag_info in datos_tweet["entities"]["hashtags"]:
                        hashtag_entry = {
                            "text": hashtag_info.get("text", None),
                        }
                        tweet_filtrado["entities"]["hashtags"].append(hashtag_entry)
                tweets_data.append(tweet_filtrado)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON in file {archivo}: {e}")
    return tweets_data
        

def crearRT(archivo_salida):
    # Cargar el archivo JSON
    with open(archivo_salida, 'r', encoding='utf-8') as file:
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
    with open('rtp.json', 'w', encoding='utf-8') as outfile:
        json.dump(final_json, outfile, indent=4, ensure_ascii=False)
    return 'rtp.json'


def crearGrafoRT(archivo_rtjson):
    # Cargar el archivo JSON de retweets
    with open(archivo_rtjson, 'r', encoding='utf-8') as file:
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
    nx.write_gexf(G, 'rtp.gexf')

def crearMencion(archivo_salida):
    # Cargar el archivo JSON
    with open(archivo_salida, 'r', encoding='utf-8') as file:
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
    with open('mencionp.json', 'w', encoding='utf-8') as outfile:
        json.dump(final_json, outfile, indent=4, ensure_ascii=False)
    return 'mencionp.json'


def crearGrafoMencion(arhivo_mencion):
    # Cargar los datos desde el archivo mencion.json
    with open(arhivo_mencion, 'r', encoding='utf-8') as file:
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
    nx.write_gexf(mention_graph, 'mencionp.gexf')





def crearCRT(archivo_rtjson):
        # Cargar el archivo JSON
    with open(archivo_rtjson, 'r', encoding='utf-8') as file:
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
    with open('corrtwp.json', 'w', encoding='utf-8') as file:
        json.dump(coretweets_dict, file, indent=4)
    return "corrtwp.json"


def crearGrafoCRT(archivo_corrtwp):
    # Cargar los datos de coretweets desde corrtw.json
    with open(archivo_corrtwp, 'r', encoding='utf-8') as file:
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
    nx.write_gexf(G, 'corrtwp.gexf')



if __name__ == "__main__":
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()
    size = comm.Get_size()
    
    
    if rank == 0:
        archivo_salida = "merged_outputp.json" 
        directorio = "./datos_copiadosp/"
        argv = sys.argv[1:]
        opts = []
        i = 0
        while i < len(argv):
            argumento = argv[i]
            valor = argv[i + 1] if i + 1 < len(argv) else ''
            if argumento.startswith('--'):
                opts.append((argumento, ''))
            else:
                if argumento.startswith('-') and not valor.startswith('-'):
                    opts.append((argumento, valor))
                    i += 2
                    continue
                elif argumento.startswith('-') and valor.startswith('-') and not valor.startswith('--'):
                    pass
                i += 1
        for opt, arg in opts:
            if opt == '-d':
                directorio_a_copiar = arg
            if opt == '-ff':
                fecha_final_str = arg
            if opt == '-fi':
                fecha_inicial_str = arg
            if opt == '-h':
                nombre_archivo_hashtags = arg.replace('.txt', '')

        for opt, arg in opts:
            if opt == '--grt':
                print('Generate retweet graph')
            if opt == '--jrt':
                print('Generate retweet json')
            if opt == '--gm':
                print('Generate mention graph')
            if opt == '--jm':
                print('Generate mention json')
            if opt == '--gcrt':
                print('Generate coretweet graph')
            if opt == '--jcrt':
                print('Generate coretweet json')
        if fecha_inicial_str:
            # Separar el día, mes y año
            dia_ini, mes_ini, anio_ini = map(int, fecha_inicial_str.split('-'))
            # Sumar 2000 al año si es menor a 50
            if anio_ini < 50:
                anio_ini += 2000
            # Formatear la fecha inicial a dd-mm-aaaa
            fecha_inicial_str = f"{dia_ini:02d}-{mes_ini:02d}-{anio_ini}"
            
        if fecha_final_str:
            dia_fin, mes_fin, anio_fin = map(int, fecha_final_str.split('-'))
            if anio_fin < 50:
                anio_fin += 2000
            fecha_final_str = f"{dia_fin:02d}-{mes_fin:02d}-{anio_fin}"

        tiempo_inicioT = time.time()
        encontrar_archivos(directorio_a_copiar,nombre_archivo_hashtags,fecha_inicial_str,fecha_final_str)

        # Proceso principal
        if nombre_archivo_hashtags:
            if not nombre_archivo_hashtags.endswith('.txt'):
                nombre_archivo_hashtags += '.txt'
        hashtags_a_buscar = []
        if os.path.exists(nombre_archivo_hashtags):
            with open(nombre_archivo_hashtags, 'r') as file:
                hashtags_a_buscar = [line.strip() for line in file.readlines()]
        fecha_inicial, fecha_final = None, None
        if fecha_inicial_str:
            fecha_inicial = datetime.strptime(fecha_inicial_str, "%d-%m-%Y").date()
        if fecha_final_str:
            fecha_final = datetime.strptime(fecha_final_str, "%d-%m-%Y").date()
        archivos_a_procesar = [os.path.join(directorio, archivo) for archivo in os.listdir(directorio) if archivo.endswith(".bz2")]
        # Dividir archivos entre procesos
        chunks = [archivos_a_procesar[i::size] for i in range(size)]
    else:
        hashtags_a_buscar = None
        fecha_inicial = None
        fecha_final = None
        chunks = None
    
    hashtags_a_buscar = comm.bcast(hashtags_a_buscar, root=0)
    fecha_inicial = comm.bcast(fecha_inicial, root=0)
    fecha_final = comm.bcast(fecha_final, root=0)
    archivos_a_procesar = comm.scatter(chunks, root=0)
    tweets_data = []

    for archivo in archivos_a_procesar:
        tweets_data.extend(merged_output(archivo, hashtags_a_buscar, fecha_inicial, fecha_final))
    # Recopilar resultados en el proceso 0
    all_tweets_data = comm.gather(tweets_data, root=0)
    if rank == 0:
        # Consolidar datos en el proceso principal y escribir en el archivo de salida
        merged_tweets = []
        for data in all_tweets_data:
            merged_tweets.extend(data)
        with open(archivo_salida, 'w', encoding='utf-8') as archivo_salida:
            json.dump(merged_tweets, archivo_salida, ensure_ascii=False, indent=2)
        #comm.Barrier()
            


        archivo_merged = "merged_outputp.json" 

            
        archivo_rtjson = crearRT(archivo_merged)
        crearGrafoRT(archivo_rtjson)
        archivo_mencion = crearMencion(archivo_merged)
        crearGrafoMencion(archivo_mencion)
        archivo_corrtw = crearCRT(archivo_rtjson)
        crearGrafoCRT(archivo_corrtw)



        tiempo_finT = time.time()
        tiempo_transcurridoT = tiempo_finT - tiempo_inicioT
        print(f"Time: {tiempo_transcurridoT} seconds")



