import os
import sys
from dotenv import load_dotenv
import paramiko

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

SFTP_HOST = os.getenv("SFTP_HOST")
SFTP_USER = os.getenv("SFTP_USER")
SFTP_PASSWORD = os.getenv("SFTP_PASSWORD")
SFTP_PORT = os.getenv("SFTP_PORT", "22")
REMOTE_DIR = "/root/pedro_leblon"

# Arquivos e diretórios que devem ser ignorados no deploy
IGNORE_PATTERNS = {
    ".git",
    ".github",
    "venv",
    ".venv",
    "__pycache__",
    ".idea",
    "database",
    "pedro_leblon.zip",
    ".env",
    "deploy.py",  # Evita subir o próprio script de deploy se desejado
}

def should_ignore(path, root_dir):
    relative_path = os.path.relpath(path, root_dir)
    parts = relative_path.split(os.sep)
    for part in parts:
        if part in IGNORE_PATTERNS or part.endswith(".pyc"):
            return True
    return False

def main():
    if not all([SFTP_HOST, SFTP_USER, SFTP_PASSWORD]):
        print("Erro: As variáveis de ambiente SFTP_HOST, SFTP_USER, e SFTP_PASSWORD devem estar definidas no arquivo .env.")
        print("Certifique-se de que o arquivo .env existe e contém esses valores.")
        sys.exit(1)

    port = int(SFTP_PORT)
    print(f"Conectando a {SFTP_HOST}:{port} via SFTP...")
    
    ssh = paramiko.SSHClient()
    # Adiciona a chave do host automaticamente se não estiver no know_hosts
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(SFTP_HOST, port=port, username=SFTP_USER, password=SFTP_PASSWORD, timeout=15)
        sftp = ssh.open_sftp()
        print("Conexão estabelecida com sucesso!")
        
        # Garante que o diretório base existe no servidor remoto
        try:
            sftp.chdir(REMOTE_DIR)
            print(f"Diretório remoto '{REMOTE_DIR}' já existe.")
        except IOError:
            print(f"Diretório remoto '{REMOTE_DIR}' não existe. Criando...")
            # Cria o diretório (supondo que o /root existe)
            sftp.mkdir(REMOTE_DIR)
            sftp.chdir(REMOTE_DIR)

        local_dir = os.path.dirname(os.path.abspath(__file__))
        
        for root, dirs, files in os.walk(local_dir):
            # Filtra os diretórios para não entrar recursivamente nos ignorados
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d), local_dir)]
            
            for file in files:
                local_file_path = os.path.join(root, file)
                if should_ignore(local_file_path, local_dir):
                    continue
                
                # Gera o caminho de destino correspondente no servidor remoto
                rel_path = os.path.relpath(local_file_path, local_dir)
                remote_file_path = os.path.join(REMOTE_DIR, rel_path).replace("\\", "/")
                remote_file_dir = os.path.dirname(remote_file_path)

                # Cria os subdiretórios remotos recursivamente se necessário
                dir_parts = remote_file_dir.strip("/").split("/")
                current_dir = ""
                for part in dir_parts:
                    current_dir += "/" + part
                    try:
                        sftp.stat(current_dir)
                    except IOError:
                        print(f"Criando diretório remoto: {current_dir}")
                        sftp.mkdir(current_dir)
                
                print(f"Enviando: {rel_path} -> {remote_file_path}")
                sftp.put(local_file_path, remote_file_path)
                
        print("\nDeploy concluído com sucesso!")
        
    except Exception as e:
        print(f"\nErro durante o deploy: {e}")
        sys.exit(1)
    finally:
        if 'sftp' in locals():
            sftp.close()
        ssh.close()

if __name__ == "__main__":
    main()
