A containerised stack consists of Application Load Balancer, ECS Cluster, API as container and RDS Aurora

1. **Application Gateway (AGW)**: The Application Gateway, also known as an Application Load Balancer, efficiently distributes incoming traffic among multiple instances of the API service running on the ECS Cluster.

2. **ECS Cluster (ECS)**: The ECS Cluster is responsible for managing and orchestrating the deployment of API containers. It ensures high availability, fault tolerance, and auto-scaling capabilities.

3. **API Service Container**: The API service is containerized, allowing for easy deployment and scalability. It encapsulates the API application and its dependencies, making it more manageable and consistent across different environments.

4. **RDS Aurora**: RDS Aurora serves as the relational database for the application. It provides a scalable, high-performance, and fully managed database solution, ensuring data persistence and integrity for the API.

The application can efficiently handle incoming requests through the Application Gateway, which distributes traffic to the API service containers hosted on the ECS Cluster. The API service interacts with the RDS Aurora database to store and retrieve data, providing a robust and scalable foundation for the containerized application stack.

<img width="792" alt="architecture" src="https://github.com/usman-akram-dev/aws-containers-example/assets/7351877/3b11cae6-5261-4ff1-9537-badd9824ade9">
