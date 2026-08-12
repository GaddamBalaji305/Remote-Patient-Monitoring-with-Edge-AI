import unittest
import os

class TestDockerStep16(unittest.TestCase):
    def test_01_dockerfiles_exist(self):
        """Verify Dockerfile existence for backend, edge-ai, and frontend services."""
        self.assertTrue(os.path.exists("backend/Dockerfile"))
        self.assertTrue(os.path.exists("edge_ai/Dockerfile"))
        self.assertTrue(os.path.exists("frontend/Dockerfile"))
        self.assertTrue(os.path.exists("frontend/nginx.conf"))

    def test_02_backend_dockerfile_contents(self):
        """Verify backend Dockerfile base image, port exposition, and CMD instructions."""
        with open("backend/Dockerfile", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("FROM python:3.12-slim", content)
        self.assertIn("EXPOSE 8000", content)
        self.assertIn("uvicorn", content)

    def test_03_frontend_nginx_configuration(self):
        """Verify Nginx configuration proxies REST API and WebSockets to backend:8000."""
        with open("frontend/nginx.conf", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("listen 3000;", content)
        self.assertIn("proxy_pass http://backend:8000/api/;", content)
        self.assertIn("proxy_pass http://backend:8000/ws/;", content)

    def test_04_docker_compose_structure(self):
        """Verify docker-compose.yml defines all 4 microservices with health checks."""
        self.assertTrue(os.path.exists("docker-compose.yml"))
        
        with open("docker-compose.yml", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("frontend:", content)
        self.assertIn("backend:", content)
        self.assertIn("edge-ai:", content)
        self.assertIn("database:", content)
        self.assertIn("3000:3000", content)
        self.assertIn("8000:8000", content)
        self.assertIn("5432:5432", content)

    def test_05_environment_variables_file(self):
        """Verify .env.docker configuration file exists and contains template environment keys."""
        self.assertTrue(os.path.exists(".env.docker"))
        with open(".env.docker", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("POSTGRES_USER", content)
        self.assertIn("DATABASE_URL", content)
        self.assertIn("SECRET_KEY", content)
        self.assertIn("BACKEND_URL", content)

    def test_06_docker_documentation_exists(self):
        """Verify docs/docker.md exists and covers startup, shutdown, and troubleshooting."""
        self.assertTrue(os.path.exists("docs/docker.md"))
        with open("docs/docker.md", "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("docker compose up --build", content)
        self.assertIn("docker compose down", content)
        self.assertIn("Environment Variables", content)
        self.assertIn("Troubleshooting", content)

if __name__ == "__main__":
    unittest.main()
