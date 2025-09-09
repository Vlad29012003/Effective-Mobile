# Docker Swarm

### Hints:

- If you use configs, when you update the config or stack, you should update config's name in the stack file.

### Initializing a Docker Swarm

```bash
  docker swarm init
```

### To add a node to the swarm

```bash
  docker swarm join --token <token> <manager-ip>:2377
```

### To list nodes in the swarm

```bash
  docker node ls
```

# Portainer Deployment and Agent

### By docker-compose

Create `portainer-agent-stack.yml`

```yml
version: '3.7'

services:
  agent:
    image: portainer/agent:lts
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/volumes:/var/lib/docker/volumes
    networks:
      - agent_network
    deploy:
      mode: global
      placement:
        constraints: [ node.platform.os == linux ]

  portainer:
    image: portainer/portainer-ce:lts
    command: -H tcp://tasks.agent:9001 --tlsskipverify
    ports:
      - "9443:9443"
      - "9000:9000"
    volumes:
      - portainer_data:/data
    networks:
      - agent_network
      - backend-net
    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints: [ node.role == manager ]

networks:
  agent_network:
    driver: overlay
    attachable: true
  backend-net:
    driver: overlay
    attachable: true

volumes:
  portainer_data:
```

### Run portainer and agent

```bash
  docker stack deploy -c portainer-agent-stack.yml portainer
```

### Access Portainer

- Open your browser and go to `http://<manager-ip>:9000`.
- Set up your admin user and password.
- Add secrets and configurations as needed.

### Create networks

```bash
  docker network create --driver overlay --attachable backend-net
```

### Run your stack

- Before run you should build your images and push them to a registry. (Check `.gitlab-ci.yml` example)
- After run the build, you can deploy your stack using the following command:
-

```bash
  docker stack deploy -c <your-stack-file>.yml <stack-name>
```

### To remove the stack

```bash
  docker stack rm <stack-name>
```

### To remove Portainer and Agent

```bash
  docker stack rm portainer
```

### To remove the network

```bash
  docker network rm backend-net
```

### To remove the volumes

```bash
  docker volume rm portainer_data
```

### To remove the swarm

```bash
  docker swarm leave --force
```
