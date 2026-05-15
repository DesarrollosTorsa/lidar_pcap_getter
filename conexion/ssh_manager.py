import paramiko
from utils.logger import info_logger, error_logger, warning_logger

def crear_cliente_ssh() -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    return ssh

def conectar_ssh(ssh: paramiko.SSHClient, hostname: str, port: int, username: str, password: str, timeout: int) -> None:
    info_logger(f"Conectando a {hostname}:{port} como {username}")
    ssh.connect(
        hostname=hostname,
        port=port,
        username=username,
        password=password,
        timeout=timeout,
        banner_timeout=300
    )

def conectar_con_salto(cliente_base, target_host, target_port, user, password, timeout=30):
    """
    Crea un cliente SSH anidado usando un túnel TCP sobre la conexión existente.
    """
    transport = cliente_base.get_transport()
    # Abrimos canal desde el servidor hacia el destino (localhost:puerto_antena)
    dest_addr = (target_host, target_port)
    local_addr = ('localhost', 0) 
    
    canal = transport.open_channel("direct-tcpip", dest_addr, local_addr)
    
    next_client = crear_cliente_ssh()
    next_client.connect(target_host, username=user, password=password, sock=canal, timeout=timeout)
    return next_client

def cerrar_ssh(ssh: paramiko.SSHClient) -> None:
    if ssh:
        ssh.close()