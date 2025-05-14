#!/usr/bin/env python3
"""
api_backend.py
This module implements a simple HTTP server that listens for incoming connections
and processes GET requests. It provides various endpoints to retrieve environment
variables, simulate health states, and terminate the container.
"""

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
    status = {'healthy': True,
              'healthy_timeout': None,
              'kill': False,
              'container_start_time': time.ctime()}
    # health_timeout = None
    # kill = False
    # container_start_time = time.ctime()

    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to the host and port
    server_socket.bind(("0.0.0.0", port))

    # Listen for incoming connections
    server_socket.listen(5)

    log(f"Container is listening on port { port }")

    while True:
        # Establish connection with client
        client_socket, addr = server_socket.accept()

        # Connection received from client
        log(f"Got a connection from { addr }")

        # Retrun to healthy state if it was sick
        if not status['healthy'] and \
        status['healthy_timeout'] and \
        time.time() > status['healthy_timeout']:
            log("Container is healthy again.")
            status = {
                'healthy': True,
                'healthy_timeout': None,
                'kill': False,
                'container_start_time': status['container_start_time']
            }

        # Data received from client
        data = client_socket.recv(1024)
        method, uri, parameters, source = analyze_request(data, addr)

        log(f"Received data from client:\n{data.decode('ascii')}\n")

        body =  f"""Time in container: {str(time.ctime())}
Container start time: {status['container_start_time']}
Requests received: {request_counter(requests_file)}
Hostname: {host}
Container port: {port}
Client source ip: {source['ip']}
Client source port: {source['port']}
URI: {uri}
Method: {method}
Health: {status['healthy']}"""
        # body =  f"Time in container: {str(time.ctime())}\n"
        # body += f"Container start time: {status['container_start_time']}\n"
        # body += f"Requests received: {request_counter(requests_file)}\n"
        # body += f"Hostname: {host}\n"
        # body += f"Container port: {port}\n"
        # body += f"Client source ip: {source['ip']}\n"
        # body += f"Client source port: {source['port']}\n"
        # body += f"URI: {uri}\n"
        # body += f"Method: {method}\n"
        # body += f"Health: {status['healthy']}\n"
        # body += "\n"

        match uri.split('/'):
            case ['']:
                body += "No GET request path provided\n"
            case ['env'] | ['api', 'env']:
                body += "Environment variables:\n"
                body += envs
            case ['api', 'kill'] | ['kill']:
                body += "\n!!! THIS CONTAINER WILL BE KILLED !!!\n"
                status['kill'] = True
            case ['api', 'health'] | ['health']:
                body = '{status: "ok"}' if status['healthy'] else '{status: "sick"}'
                log(body)
            case ['api', 'unhealthy'] | ['unhealthy']:
                body += 'Change state to unhealty'
                status['healthy'] = False
                if 'time' in parameters.keys():
                    try:
                        status['healthy_timeout'] = time.time() + int(parameters['time'])
                        body += f'Sick for {parameters["time"]} seconds'
                    except TypeError:
                        body += 'time was set but not in a valid way'
                        status['healthy_timeout'] = None
                else:
                    status['healthy_timeout'] = None

        send_response(client_socket, body, status['healthy_timeout'])

        if status['kill']:
            break
    log("Stopping application")
    server_socket.close()
    os._exit(1)


def send_response(client_socket, body: str, health: bool) -> None:
    """
    Send an HTTP response to the client.
    :param client_socket: The socket object for the client connection.
    :param body: The body of the HTTP response.
    :param health: The health status of the container.
    """
    response_headers = {
        'Content-Type': 'text/text; encoding=utf8',
        'Content-Length': len(body),
        'Connection': 'close',
    }

    response_headers_raw = ''.join(f'{k}: {v}\r\n' for k, v in response_headers.items())
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


def analyze_request(data: bytes, addr: bytes) -> tuple:
    """
    Analyze the incoming request data and extract relevant information.
    :param data: The incoming request data as bytes.
    :return: A tuple containing the HTTP method, request path, and source IP address.
    """

    # Decode the incoming data to ASCII
    data_lines = data.decode('ascii').split('\n')
    source_ip = None
    method, request, *_ = data_lines[0].split(' ')

    if '?' in request:
        parameters = request.split('?')[1].split('&')
        parameters = {x.split('=')[0]: x.split('=')[1] for x in parameters}
        request = request.split('?')[0]
    else:
        parameters = None
    for line in data_lines[1:]:
        if line.startswith('X-Forwarded-For: ') and not source_ip:
            source_ip = line.split(' ')[1]
        if line.startswith('X-Real-IP: '):
            source_ip = line.split(' ')[1]

    if not source_ip:
        source_ip = str(addr[0])
    source_port = str(addr[1])
    source = {'ip': source_ip, 'port': source_port}

    return method, request, parameters, source


def init_variabeles()-> tuple:
    """
    Initialize variables from environment variables.
    :return: tuple containing port, requests_file and envs
    """

    # Define the port on which the server will listen
    port = int(os.getenv('PORT', "5000"))

    # Define the file where request count will be stored
    requests_file = os.getenv('REQUESTS_FILE', '/data/requests.txt')

    # Get all environment variables
    envs = []
    for name, value in os.environ.items():
        envs.append({'name': name, 'value': value})

    # Sort the environment vars by name
    envs = sorted(envs, key=lambda x: x['name'])
    return_env = ""

    for env in envs:
        return_env += f"{env['name']}: {env['value']}\n"

    # Get the hostname of the container
    host = socket.gethostname()

    return port, requests_file, return_env, host



def request_counter(requests_file:str) -> int:
    """
    Increment and track the number of requests in a file.
    This function checks if the specified file exists. If it does not exist,
    it creates the file and initializes it with the value '0'. Then, it reads
    the current request count from the file, increments it by one, writes the
    updated count back to the file, and returns the new count.
    Args:
        requests_file (str): The path to the file used to store the request count.
    Returns:
        int: The updated request count after incrementing.
    """

    # Check if the requests file exists
    if not os.path.exists(requests_file):
        with open(requests_file, 'w', encoding='UTF-8') as f:
            f.write('1')
        return 1

    with open(requests_file, 'r', encoding='UTF-8') as f:
        requests = int(f.read())
    requests += 1
    with open(requests_file, 'w', encoding='UTF-8') as f:
        f.write(str(requests))
    return requests


def log(msg):
    """
    Log a message with a timestamp.
    :param msg: The message to log.
    """

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
    """
    Get the current date and time in a specific format.
    :return: Current date and time as a string.
    """

    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    main()
