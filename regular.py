import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import threading
import os
import hashlib
import base64

# Função para calcular o checksum SHA-256 de um arquivo dado o seu caminho
def calculate_checksum(file_path):
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(4096), b""):
                sha256.update(block)
    except OSError as e:
        print(f"Could not read file {file_path}: {e}")
        return None
    return sha256.hexdigest()

# Função para obter os arquivos locais no diretório atual com seus checksums
def get_local_files():
    files = {}
    for file in os.listdir('.'):
        if os.path.isfile(file):
            checksum = calculate_checksum(file)
            if checksum is not None:
                files[file] = checksum
    return files

# Função para registrar o nó local com o nó de borda
def register_with_edge_node(edge_node_host, edge_node_port, node_host, node_port):
    with xmlrpc.client.ServerProxy(f'http://{edge_node_host}:{edge_node_port}/') as proxy:
        local_files = get_local_files()
        proxy.register_node(node_host, node_port, local_files)  # Registra o nó com seus arquivos locais
        for file, checksum in local_files.items():
            proxy.register_file(node_host, node_port, file, checksum)  # Registra cada arquivo com seu checksum

# Função para baixar um arquivo de um nó remoto
def download_file_from_node(node_host, node_port, filename):
    try:
        with xmlrpc.client.ServerProxy(f'http://{node_host}:{node_port}/') as proxy:
            file_data = proxy.download(filename)  # Chama o método remoto 'download' para obter os dados do arquivo
            file_data_bytes = base64.b64decode(file_data)  # Decodifica os dados do arquivo codificados em base64
            with open(filename, 'wb') as f:
                f.write(file_data_bytes)  # Escreve os dados do arquivo decodificados no arquivo local
            return f"File '{filename}' downloaded successfully."
    except xmlrpc.client.Fault as fault:
        return f"XML-RPC Fault: {fault.faultString} (code: {fault.faultCode})"
    except xmlrpc.client.ProtocolError as err:
        return f"A protocol error occurred: {err.errmsg}"
    except Exception as e:
        return f"An error occurred: {e}"

# Função para lidar com solicitações de download recebidas
def handle_download_request(filename):
    print(f"Received download request for file: {filename}")
    return download_file(filename)

# Função para iniciar o nó local com um servidor XML-RPC
def start_node(node_host, node_port, edge_node_host, edge_node_port):
    server = SimpleXMLRPCServer((node_host, node_port), allow_none=True)
    
    # Função para baixar um arquivo solicitado
    def download_file(filename):
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')  # Codifica o arquivo em base64 e retorna como string
        else:
            raise FileNotFoundError(f"File '{filename}' not found on this node.")

    server.register_function(download_file, "download")  # Registra a função 'download' para chamadas remotas
    
    threading.Thread(target=server.serve_forever).start()  # Inicia o servidor em uma thread separada
    register_with_edge_node(edge_node_host, edge_node_port, node_host, node_port)  # Registra este nó com o nó de borda
    print(f"Node running on {node_host}:{node_port}")  # Mensagem indicando que o nó está em execução

if __name__ == "__main__":
    node_host = '10.62.202.21'  # Endereço IP do nó local
    node_port = 8002  # Porta do servidor XML-RPC no nó local
    edge_node_host = '10.62.202.21'  # Endereço IP do nó de borda
    edge_node_port = 8000  # Porta do servidor XML-RPC no nó de borda
    start_node(node_host, node_port, edge_node_host, edge_node_port)  # Inicia o nó local
    
    while True:
        filename = input("Enter the name of the file to download (or 'exit' to quit): ")
        if filename.lower() == 'exit':
            break
        
        try:
            with xmlrpc.client.ServerProxy(f'http://{edge_node_host}:{edge_node_port}/') as proxy:
                node_info = proxy.find_node_with_file(filename)  # Busca informações sobre o nó que possui o arquivo
                if node_info:
                    node_host, node_port = node_info
                    print(f"File '{filename}' found at node {node_host}:{node_port}. Downloading...")
                    result = download_file_from_node(node_host, node_port, filename)  # Baixa o arquivo do nó encontrado
                    print(result)
                else:
                    print(f"File '{filename}' not found in the network.")
        except Exception as e:
            print(f"Error communicating with edge node: {e}")
