# Bay Wheels MCP Server

This is an MCP server that provides access to Bay Wheels realtime bikeshare data.

## Features

- Find nearest bike (standard or ebike)
- Find nearest dock with available spaces
- Supports checking for free bikes (dockless) when looking for a single bike

## Setup

### For Claude Desktop (Local Development)

Add this to your Claude Desktop configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "bay-wheels": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "--directory",
        "/path/to/bay-wheels-mcp",
        "run",
        "server.py"
      ]
    }
  }
}
```

Make sure to update the path to match your local installation directory.

### Manual Testing (stdio)

You can run the server directly for testing with Claude Desktop:

```bash
uv run server.py
```

## Deployment

### Docker Deployment

#### Quick Start
```bash
# Build the image
docker build -t bay-wheels-mcp .

# Run the container
docker run -p 8000:8000 bay-wheels-mcp

# Test the health check
curl http://localhost:8000/health
```

#### Using Docker Compose
```bash
# Start the server
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop the server
docker-compose down
```

#### Environment Variables
- `PORT` - Server port (default: 8000)
- `HOST` - Bind host (default: 0.0.0.0)

#### Health Check
The server exposes a health check endpoint at `/health` for container orchestration:
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","service":"bay-wheels-mcp","version":"0.1.0"}
```

### Platform-Specific Deployment

#### AWS ECS/Fargate
1. Push image to ECR:
```bash
docker build -t bay-wheels-mcp .
docker tag bay-wheels-mcp:latest <aws-account>.dkr.ecr.<region>.amazonaws.com/bay-wheels-mcp:latest
docker push <aws-account>.dkr.ecr.<region>.amazonaws.com/bay-wheels-mcp:latest
```

2. Create ECS task definition with health check enabled
3. Deploy as ECS service with load balancer

#### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/<project-id>/bay-wheels-mcp
gcloud run deploy bay-wheels-mcp --image gcr.io/<project-id>/bay-wheels-mcp --port 8000
```

#### Fly.io
```bash
fly launch --dockerfile Dockerfile
fly deploy
```

#### Azure Container Instances
Use Azure Portal or Azure CLI to deploy the Docker image with port 8000 exposed.

### Connecting Mobile Apps

The deployed server uses StreamableHTTP transport. Configure your MCP client to connect to:

```
URL: https://your-deployed-server.com/mcp
```

**Note**: The MCP endpoint is at `/mcp`, not the root path.

See [MCP documentation](https://modelcontextprotocol.io) for client integration details.

## Testing

### Testing the Deployed Server

The simplest way to test is using the health check endpoint:

```bash
# Test that the server is running
curl https://your-server.com/health
# Should return: {"status":"healthy","service":"bay-wheels-mcp","version":"0.1.0"}
```

For full MCP protocol testing, use an MCP client (Claude Desktop, mobile app, or custom client). The StreamableHTTP transport requires session management and proper header negotiation which is best handled by official MCP clients.

### Testing with MCP Clients

The best way to test the deployed server is to configure it in your MCP client:

#### Claude Desktop (Remote Server)
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "bay-wheels-remote": {
      "url": "https://your-server.com/mcp",
      "transport": "streamable-http"
    }
  }
}
```

#### Mobile App
Configure your mobile app's MCP client to connect to:
```
https://your-server.com/mcp
```

Then test the tools by asking Claude:
- "Find me the nearest Bay Wheels bike near the Ferry Building in SF"
- "Where can I return a bike near Dolores Park?"

## Tools

### `find_nearest_bike`
Finds the nearest bike availability.
- `latitude`: float
- `longitude`: float
- `count`: int (default 1)
- `bike_type`: str (optional, "classic_bike" or "electric_bike")

### `find_nearest_dock_spaces`
Finds the nearest dock with return spaces.
- `latitude`: float
- `longitude`: float
- `count`: int (default 1)
