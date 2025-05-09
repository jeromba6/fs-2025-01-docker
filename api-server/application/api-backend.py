#!/usr/bin/env python3
import socket
import time
import os
import datetime

def main():
    # Define the port on which the server will listen
    port = int(os.getenv('PORT', 5000))
    requests_file = os.getenv('REQUESTS_FILE', '/data/requests.txt')
    envs = []
    cm_vars = []
    for name, value in os.environ.items():
        envs.append({'name': name, 'value': value})
        if name.startswith('CM_VAR_'):
            cm_vars.append({'name': name, 'value': value})

    # Sort the CM_VAR_ vars by name
    envs = sorted(envs, key=lambda x: x['name'])
    cm_vars = sorted(cm_vars, key=lambda x: x['name'])
    kill = False
    container_start_time = time.ctime()

    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Get the hostname of the server
    host = socket.gethostname()

    # Bind the socket to the host and port
    server_socket.bind(("0.0.0.0", port))

    # Listen for incoming connections
    server_socket.listen(5)

    health = True

    log(f"Container is listening on port { port}")

    while True:
        # Establish connection with client
        client_socket, addr = server_socket.accept()

        # Connection received from client
        log("Got a connection from %s" % str(addr))

        # Data received from client
        data = client_socket.recv(1024)
        data_lines = data.decode('ascii').split('\n')
        get_request = None
        source_ip = None
        for line in data_lines:
            if line.startswith('GET '):
                get_request = line.split(' ')[1].split('?')[0]
                get_request_path = get_request.split('/')
                get_request_path = [x for x in get_request_path if x]
            if line.startswith('X-Forwarded-For: ') and not source_ip:
                source_ip = line.split(' ')[1]
            if line.startswith('X-Real-IP: '):
                source_ip = line.split(' ')[1]

        if not source_ip:
            source_ip = str(addr[0])
        source_port = str(addr[1])

        log(f"Received data from client:\n{data.decode('ascii')}\n")

        body =  f"Time in container: {str(time.ctime())}\n"
        body += f"Container start time: {container_start_time}\n"
        body += f"Requests received: {requests(requests_file)}\n"
        body += f"Hostname: {host}\n"
        body += f"Container port: {port}\n"
        body += f"Client source ip: {source_ip}\n"
        body += f"Client source port: {source_port}\n"
        body += f"GET request: {get_request}\n"
        body += "\n"

        match get_request_path:
            case ['']:
                body += "No GET request path provided\n"
            case ['env'] | ['api', 'env']:
                body += "Environment variables:\n"
                for env in envs:
                    body += f"{env['name']}: {env['value']}\n"
            case ['api', 'kill'] | ['kill']:
                body += "Environment variables:\n"
                for env in envs:
                    body += f"{env['name']}: {env['value']}\n"
                body += "\n!!! THIS CONTAINER WILL BE KILLED !!!\n"
                kill = True
            case ['api', 'health'] | ['health']:
                body = '{status: "ok"}' if health else '{status: "sick"}'
            case ['api', 'unhealthy'] | ['unhealthy']:
                body += 'Change state to unhealty'
                health = False

        response_headers = {
            'Content-Type': 'text/text; encoding=utf8',
            'Content-Length': len(body),
            'Connection': 'close',
        }

        response_headers_raw = ''.join('%s: %s\r\n' % (k, v) for k, v in response_headers.items())
        response_proto = 'HTTP/1.1'
        response_status = '200' if health else '500'
        response_status_text = 'OK' if health else 'Internal server error'

        # sending all this stuff
        response = f"{response_proto} {response_status} {response_status_text}\r\n"
        client_socket.sendall(response.encode())
        client_socket.sendall(response_headers_raw.encode())
        client_socket.sendall(b'\r\n') # to separate headers from body
        client_socket.send(body.encode(encoding="utf-8"))

        # Close the connection
        client_socket.close()
        if kill:
            break
    log("Stopping application")
    server_socket.close()
    os._exit(1)


def requests(requests_file:str) -> int:
    if not os.path.exists(requests_file):
        with open(requests_file, 'w') as f:
            f.write('0')
    with open(requests_file, 'r') as f:
        requests = int(f.read())
    requests += 1
    with open(requests_file, 'w') as f:
        f.write(str(requests))
    return requests


def log(msg):
    print(f'{now()} {msg}')


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    main()