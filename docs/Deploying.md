# Deploying the Application

- After deploying to the server, please close port 80 and 443 in the firewall.
- Read Swarm documentation for more details on deploying the application.
- When you updating the nginx in swarm, you need to clean configuration files in the container.
- After updating stacks, you need to restart the nginx container. (You can do it with portainer).
