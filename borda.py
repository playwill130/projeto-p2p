from xmlrpc.server import SimpleXMLRPCServer  # Importa o servidor XML-RPC
import threading  # Importa threading para suporte a múltiplos threads
import xmlrpc.client  # Importa cliente XML-RPC para comunicação
import time  # Importa time para operações de tempo

nodes = {}  # Dicionário para armazenar nós registrados
files = {}  # Dicionário para armazenar arquivos registrados

def register_node(node_host, node_port, node_files):
    """
    Função para registrar um novo nó com seus arquivos.
    """
    nodes[(node_host, node_port)] = node_files  # Adiciona o nó ao dicionário de nós
    return True  # Retorna True para indicar sucesso

def register_file(node_host, node_port, filename, checksum):
    """
    Função para registrar um novo arquivo em um nó específico.
    """
    if filename not in files:
        files[filename] = []  # Cria uma lista vazia se o arquivo não existir ainda
    files[filename].append((node_host, node_port, checksum))  # Adiciona o arquivo à lista de arquivos
    return True  # Retorna True para indicar sucesso

def find_file(filename):
    """
    Função para encontrar informações sobre um arquivo específico.
    """
    if filename in files:
        return files[filename]  # Retorna a lista de nós que possuem o arquivo
    return []  # Retorna uma lista vazia se o arquivo não existir

def periodic_file_check():
    """
    Função executada periodicamente para verificar os arquivos em nós registrados.
    """
    while True:
        print("checando arquivos:")
        for (node_host, node_port), node_files in nodes.items():
            print(f"Node at {node_host}:{node_port} has files:")
            for filename, checksum in node_files.items():
                print(f"- {filename}")  # Mostra os arquivos que o nó possui
        print("")

        time.sleep(5)  # Aguarda 5 segundos entre as verificações

def find_node_with_file(filename):
    """
    Função para encontrar um nó que possui um arquivo específico.
    """
    for (node_host, node_port), node_files in nodes.items():
        if filename in node_files:
            return (node_host, node_port)  # Retorna o host e porta do nó que possui o arquivo
    return None  # Retorna None se o arquivo não for encontrado em nenhum nó

def start_edge_node(edge_node_host, edge_node_port):
    """
    Função para iniciar um nó de borda com um servidor XML-RPC.
    """
    server = SimpleXMLRPCServer((edge_node_host, edge_node_port), allow_none=True)  # Cria o servidor XML-RPC
    server.register_function(register_node, "register_node")  # Registra a função register_node
    server.register_function(register_file, "register_file")  # Registra a função register_file
    server.register_function(find_file, "find_file")  # Registra a função find_file
    server.register_function(find_node_with_file, "find_node_with_file")  # Registra a função find_node_with_file
    
    threading.Thread(target=server.serve_forever).start()  # Inicia o servidor em uma nova thread
    threading.Thread(target=periodic_file_check).start()  # Inicia a verificação periódica em uma nova thread
    print(f"Edge node running on {edge_node_host}:{edge_node_port}")  # Mensagem de inicialização do nó de borda

if __name__ == "__main__":
    edge_node_host = '10.62.202.21'  # Endereço IP do nó de borda
    edge_node_port = 8000  # Porta do servidor XML-RPC no nó de borda
    start_edge_node(edge_node_host, edge_node_port)  # Inicia o nó de borda
    input("Pressione Enter para sair...\n")  # Espera por uma entrada para sair
