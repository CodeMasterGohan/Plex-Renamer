# Plex Media Renamer - Web Application

A modern, containerized web application that automatically renames movie and TV show files according to Plex naming conventions using metadata from TMDB and TVDB APIs. This application has been converted from a desktop GUI to a beautiful, responsive web interface with Docker support.

## ✨ Features

### 🎬 **Media Processing**
- **Multi-Source Metadata**: Integrates with TMDB and TVDB APIs for comprehensive movie and TV show information
- **Plex Naming Compliance**: Automatically renames files according to Plex naming conventions
- **Smart File Detection**: Automatically detects movies vs TV shows and extracts season/episode information
- **Flexible Organization**: Separate handling for movies and TV shows with configurable folder structures

### 🌐 **Modern Web Interface**
- **Responsive Design**: Beautiful, mobile-friendly interface using Bootstrap 5
- **Dark/Light Mode**: Toggle between themes with persistent preference storage
- **Real-time Progress**: Live scanning progress with detailed status updates
- **Interactive File Management**: Select individual files or batch operations
- **Directory Browser**: Built-in file system browser for easy path selection

### 🔧 **Advanced Configuration**
- **Dry Run Mode**: Preview all changes before execution with detailed comparison
- **Configurable Settings**: Customizable paths, API keys, naming preferences, and behavior
- **Multiple Language Support**: TMDB API supports multiple languages for metadata
- **Flexible Folder Structure**: Options for individual movie folders and series organization

### 🐳 **Docker & Deployment**
- **Containerized**: Fully containerized with Docker and Docker Compose
- **Volume Mounting**: Easy integration with existing Plex media directories
- **Health Checks**: Built-in health monitoring and automatic restart capabilities
- **Security**: Runs as non-root user with proper file permissions
- **Production Ready**: Optimized with Gunicorn WSGI server

### 🛡️ **Reliability & Safety**
- **Comprehensive Logging**: Track all operations and errors with detailed logs
- **Error Handling**: Robust error handling with user-friendly feedback
- **File Safety**: Checks for existing files and prevents overwrites
- **Backup Support**: Optional backup of original filenames

## 🚀 Quick Start

### Prerequisites

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Plex Media Directory** accessible to the host system

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Plex-Renamer
```

### 2. Configure Environment

Copy the example environment file and update it with your settings:

```bash
cp env.example .env
```

Edit `.env` and set your Plex media path:

```bash
# Required: Path to your Plex media directory
PLEX_MEDIA_PATH=/path/to/your/plex/media

# Optional: Security and customization
SECRET_KEY=your-very-secure-secret-key-here
TZ=America/New_York
```

### 3. Start the Application

```bash
docker-compose up -d
```

The application will be available at: **http://localhost:8080**

### 4. Initial Configuration

1. Open your browser and navigate to `http://localhost:8080`
2. Click the **Settings** button in the top navigation
3. Configure your API keys:
   - **TMDB API Key**: Get from [TMDB API Settings](https://www.themoviedb.org/settings/api)
   - **TVDB API Key**: Get from [TVDB API Key](https://thetvdb.com/dashboard/account/apikey)
4. Set your media paths:
   - **Base Media Path**: `/media/plex` (this is the mounted path inside the container)
   - **Movies Subfolder**: `movies` (or your preferred subfolder)
   - **TV Shows Subfolder**: `tv_shows` (or your preferred subfolder)
5. Save your settings

## 📖 Usage Guide

### Scanning Media Files

1. **Select Media Type**: Choose between Movies or TV Shows
2. **Verify Path**: Ensure the scan path shows your media directory
3. **Start Scan**: Click "Scan Files" to begin the process
4. **Monitor Progress**: Watch the real-time progress bar and status updates

### Managing Results

- **Select Files**: Use checkboxes to select individual files or "Select All"
- **Preview Changes**: Click "Preview" to see exactly what will be renamed
- **Dry Run Mode**: Keep enabled to test changes without actually renaming files
- **Apply Changes**: When ready, disable dry run mode and click "Apply Changes"

### File Details

Click the info button (ⓘ) next to any file to view:
- Original and proposed file paths
- Extracted media information (title, year, season, episode)
- Metadata from TMDB/TVDB APIs

## 🔧 Configuration Options

### API Settings
- **TMDB API Key**: Required for movie metadata and TV show fallback
- **TVDB API Key**: Preferred for TV show metadata
- **Preferred Language**: Language for metadata (en-US, es-ES, fr-FR, etc.)

### Path Configuration
- **Base Media Path**: Root directory for all media
- **Movies Subfolder**: Subdirectory for movies within base path
- **TV Shows Subfolder**: Subdirectory for TV shows within base path

### Behavior Settings
- **Create Movie Folders**: Create individual folders for each movie
- **Include Episode Titles**: Add episode titles to TV show filenames
- **Include Series ID**: Add TMDB/TVDB IDs to TV show folder names
- **Preferred ID Source**: Choose between TVDB or TMDB for series IDs

## 📁 Naming Conventions

### Movies
- **With Folder**: `movies/Movie Title (2023)/Movie Title (2023).ext`
- **Without Folder**: `movies/Movie Title (2023).ext`

### TV Shows
- **Standard**: `tv_shows/Show Name (2023)/Season 01/Show Name - s01e01 - Episode Title.ext`
- **With Series ID**: `tv_shows/Show Name (2023) {tvdb-12345}/Season 01/Show Name - s01e01 - Episode Title.ext`
- **Without Episode Title**: `tv_shows/Show Name (2023)/Season 01/Show Name - s01e01.ext`

## 🐳 Docker Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PLEX_MEDIA_PATH` | Host path to Plex media directory | `./plex_media_data` |
| `SECRET_KEY` | Flask secret key for sessions | `your-secret-key-change-in-production` |
| `TZ` | Timezone for the container | `UTC` |
| `FLASK_ENV` | Flask environment | `production` |
| `FLASK_DEBUG` | Enable Flask debug mode | `false` |

### Volume Mounts

- **Media Directory**: `${PLEX_MEDIA_PATH}:/media/plex:rw`
- **Configuration**: `./config:/app/config:rw`
- **Logs**: `./logs:/app/logs:rw`

### Common Setups

#### Windows
```bash
PLEX_MEDIA_PATH=C:\Plex\Media
```

#### macOS
```bash
PLEX_MEDIA_PATH=/Users/username/Plex/Media
```

#### Linux
```bash
PLEX_MEDIA_PATH=/home/username/plex/media
```

#### Synology NAS
```bash
PLEX_MEDIA_PATH=/volume1/Plex
```

#### QNAP NAS
```bash
PLEX_MEDIA_PATH=/share/Multimedia/Plex
```

## 🔍 Troubleshooting

### Common Issues

**Application won't start:**
- Check Docker and Docker Compose are installed and running
- Verify the `PLEX_MEDIA_PATH` exists and is accessible
- Check logs: `docker-compose logs plex-renamer`

**Can't access media files:**
- Ensure the media path is correctly mounted
- Check file permissions on the host directory
- Verify the path inside the container: `docker exec -it plex-media-renamer ls -la /media/plex`

**API errors:**
- Verify your TMDB and TVDB API keys are correct
- Check your internet connection
- Ensure API keys have proper permissions

**Files not being renamed:**
- Check that dry run mode is disabled
- Verify file permissions allow writing
- Review logs for specific error messages

### Viewing Logs

```bash
# View application logs
docker-compose logs plex-renamer

# Follow logs in real-time
docker-compose logs -f plex-renamer

# View logs inside container
docker exec -it plex-media-renamer tail -f /app/logs/app.log
```

### Accessing the Container

```bash
# Open a shell in the container
docker exec -it plex-media-renamer bash

# Check mounted volumes
docker exec -it plex-media-renamer ls -la /media/plex
```

## 🛠️ Development

### Running Locally

For development without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=true

# Run the application
python app.py
```

### Building Custom Image

```bash
# Build the Docker image
docker build -t plex-renamer:custom .

# Run with custom image
docker run -p 8080:5000 -v /path/to/media:/media/plex plex-renamer:custom
```

## 📝 API Documentation

The application provides a REST API for programmatic access:

- `GET /api/health` - Health check
- `GET /api/config` - Get configuration
- `POST /api/config` - Update configuration
- `POST /api/scan` - Start media scan
- `GET /api/scan/status` - Get scan status
- `GET /api/scan/results` - Get scan results
- `POST /api/rename` - Apply rename operations
- `POST /api/browse` - Browse directories

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **TMDB** for providing comprehensive movie and TV show metadata
- **TVDB** for detailed TV series information
- **Bootstrap** for the beautiful UI framework
- **Flask** for the lightweight web framework
- **Docker** for containerization support

---

**Need Help?** Open an issue on GitHub or check the troubleshooting section above. 