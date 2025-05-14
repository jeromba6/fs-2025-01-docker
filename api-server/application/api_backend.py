#!/usr/bin/env python3
import socket
import time
import os
import datetime

def main():
    """
    This module implements a simple HTTP server that listens for incoming connections
    and processes GET requests. It provides various endpoints to retrieve environment
    variables, simulate health states, and terminate the container.

    The server listens on a configurable port and logs incoming requests. It also
    handles specific GET request paths to perform actions such as returning environment
    variables, changing health states, or shutting down the server.

    Environment Variables:
    - PORT: The port on which the server listens (default: 5000).
    - REQUESTS_FILE: Path to the file where request counts are stored (default: /data/requests.txt).

    Endpoints:
    - `/`: Returns basic container information.
    - `/env` or `/api/env`: Returns all environment variables.
    - `/kill` or `/api/kill`: Returns environment variables and terminates the container.
    - `/health` or `/api/health`: Returns the health status of the container.
    - `/unhealthy` or `/api/unhealthy`: Sets the container to an unhealthy state, optionally for a
      specified duration.
    """

    # Define the port on which the server will listen
    port, requests_file, envs, host = init_variabeles()

    # Set the timeout for the health check
    health_timeout = None
    kill = False
    container_start_time = time.ctime()

    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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

        # Retrun to healthy state if it was sick
        if not health and health_timeout and time.time() > health_timeout:
            log("Container is healthy again.")
            health = True
            health_timeout = None

        # Data received from client
        data = client_socket.recv(1024)
        data_lines = data.decode('ascii').split('\n')
        get_request = None
        source_ip = None
        for line in data_lines:
            if line.startswith('GET '):
                if '?' in line:
                    parameters = line.split(' ')[1].split('?')[1].split('&')
                    parameters = {x.split('=')[0]: x.split('=')[1] for x in parameters}
                else:
                    parmeters = None
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
                log(body)
            case ['api', 'unhealthy'] | ['unhealthy']:
                body += 'Change state to unhealty'
                health = False
                if 'time' in parameters.keys():
                    try:
                        duration = int(parameters['time'])
                        health_timeout = time.time() + duration
                        body += f'Sick for {duration} seconds'
                    except:
                        body += 'time was set but not in a valid way'
                        health_timeout = None
                else:
                    health_timeout = None


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


def init_variabeles()-> tuple:
    """
    Initialize variables from environment variables.
    :return: tuple containing port, requests_file and envs
    """

    # Define the port on which the server will listen
    port = int(os.getenv('PORT', 5000))

    # Define the file where request count will be stored
    requests_file = os.getenv('REQUESTS_FILE', '/data/requests.txt')

    # Get all environment variables
    envs = []
    for name, value in os.environ.items():
        envs.append({'name': name, 'value': value})

    # Sort the environment vars by name
    envs = sorted(envs, key=lambda x: x['name'])

    # Get the hostname of the container
    host = socket.gethostname()

    return port, requests_file, envs, host



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
    # Remove empty lines
    msg = msg.strip()
    ts = now()
    spaces = ' ' * (len(ts) + 3)
    # When new line in msg add spaces to the beginning of each line after the first
    if '\n' in msg:
        msg = '\n'.join([msg.split('\n')[0]] + [spaces + x for x in msg.split('\n')[1:]])
    # Add timestamp to the message
    print(f'{ts} - {msg}')


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    main()
