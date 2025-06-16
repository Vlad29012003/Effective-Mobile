# Docker Swarm

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
